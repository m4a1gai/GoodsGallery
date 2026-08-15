"""Orchestrates pipeline runs: fetch -> RawProduct -> normalize -> Candidate
-> dedup against the existing catalog.

Two entry points:
  - `run_manual_import`: one human-supplied URL, always via ManualImportAdapter.
  - `run_discovery_crawl`: an adapter walks its own `discover()` (e.g. paging
    through a collection listing) and every URL it finds gets fetched. This
    only runs for a source whose `crawl_policy` is `auto` in the database —
    it refuses otherwise — and only when a human explicitly calls it (a CLI
    script or the Sources page's "Run Crawl" button). There is no scheduler
    anywhere in this codebase; "auto" describes what an adapter is *allowed*
    to do in one run, not that anything runs unattended.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem
from app.models.enums import CrawlPolicy
from app.models.lookup import Character, ItemType, Source
from app.models.pipeline import Candidate, DuplicateReviewPair, RawProduct
from pipeline.dedup.matcher import (
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
    MatchableFields,
    find_best_match,
)
from pipeline.normalize.normalizer import normalize
from pipeline.sources.base import DiscoveryParams, FetchResult, NotModified, RawProductDraft, SourceAdapter
from pipeline.sources.manual_import import ManualImportAdapter

logger = logging.getLogger(__name__)


def _existing_catalog_matchables(db: Session) -> list[tuple[int, MatchableFields]]:
    items = list(db.scalars(select(CatalogItem)))
    type_by_id = {t.id: t.code for t in db.scalars(select(ItemType))}
    out = []
    for item in items:
        out.append(
            (
                item.id,
                MatchableFields(
                    canonical_name=item.canonical_name,
                    japanese_name=item.japanese_name,
                    product_number=item.product_number,
                    item_type_code=type_by_id.get(item.item_type_id) if item.item_type_id else None,
                    character_ids=item.character_ids,
                ),
            )
        )
    return out


def _ingest_draft(db: Session, source: Source, draft: RawProductDraft, parser_version: str) -> Candidate:
    raw = RawProduct(
        source_id=source.id,
        source_url=draft.source_url,
        raw_title=draft.raw_title,
        raw_description=draft.raw_description,
        raw_price=draft.raw_price,
        raw_currency=draft.raw_currency,
        raw_images=draft.raw_images,
        raw_metadata=draft.raw_metadata,
        raw_html_hash=draft.raw_html_hash,
        parser_version=parser_version,
    )
    db.add(raw)
    db.flush()

    characters = list(db.scalars(select(Character)))
    normalized = normalize(raw, characters)
    item_type = (
        db.scalar(select(ItemType).where(ItemType.code == normalized.item_type_code))
        if normalized.item_type_code
        else None
    )

    candidate = Candidate(
        raw_product_id=raw.id,
        canonical_name=normalized.canonical_name,
        japanese_name=normalized.japanese_name,
        character_ids=normalized.character_ids,
        item_type_id=item_type.id if item_type else None,
        product_number=normalized.product_number,
        price=raw.raw_price,
        currency=raw.raw_currency,
        images=draft.raw_images,
        confidence=normalized.base_confidence,
    )
    db.add(candidate)
    db.flush()

    matchable = MatchableFields(
        canonical_name=candidate.canonical_name,
        japanese_name=candidate.japanese_name,
        product_number=candidate.product_number,
        item_type_code=normalized.item_type_code,
        character_ids=candidate.character_ids,
        source_url=raw.source_url,
    )
    match = find_best_match(matchable, _existing_catalog_matchables(db))

    if match and match.confidence >= AUTO_MERGE_THRESHOLD:
        from app.services.review import merge_candidate

        catalog_item = db.get(CatalogItem, match.catalog_item_id)
        merge_candidate(db, candidate, catalog_item)
    elif match and match.confidence >= REVIEW_THRESHOLD:
        db.add(
            DuplicateReviewPair(
                candidate_id=candidate.id,
                matched_catalog_item_id=match.catalog_item_id,
                similarity_score=match.confidence,
                match_reason=match.reason,
            )
        )

    return candidate


async def _fetch_and_ingest(db: Session, source: Source, adapter: SourceAdapter, url: str, parser_version: str) -> Candidate:
    fetch_result = await adapter.fetch(url)
    if fetch_result is NotModified:
        raise RuntimeError(f"{url} reported not modified on first fetch; unexpected")
    assert isinstance(fetch_result, FetchResult)
    draft = adapter.parse(fetch_result)
    return _ingest_draft(db, source, draft, parser_version)


async def run_manual_import(db: Session, source_key: str, url: str) -> Candidate:
    source = db.scalar(select(Source).where(Source.key == source_key))
    if source is None:
        raise ValueError(f"Unknown source key: {source_key}")

    candidate = await _fetch_and_ingest(db, source, ManualImportAdapter(), url, parser_version="manual_import-v1")
    db.commit()
    db.refresh(candidate)
    return candidate


async def run_discovery_crawl(
    db: Session,
    source_key: str,
    adapter: SourceAdapter,
    params: DiscoveryParams,
    limit: int | None = None,
) -> dict:
    """Bulk-import every product an adapter's discover() finds. Refuses to run
    unless the source's crawl_policy is `auto` in the database — flipping
    that flag is a deliberate, per-source decision (see Source.notes for the
    robots.txt/ToS check backing it), not something this function decides.
    """
    source = db.scalar(select(Source).where(Source.key == source_key))
    if source is None:
        raise ValueError(f"Unknown source key: {source_key}")
    if source.crawl_policy != CrawlPolicy.auto:
        raise PermissionError(
            f"Source {source_key!r} crawl_policy is {source.crawl_policy.value!r}, not 'auto'; "
            "refusing to bulk-crawl. Use run_manual_import for one URL at a time instead."
        )

    discovered = await adapter.discover(params)
    if limit:
        discovered = discovered[:limit]

    already_seen = {
        row[0] for row in db.execute(select(RawProduct.source_url).where(RawProduct.source_id == source.id))
    }

    created: list[Candidate] = []
    skipped_seen = 0
    errors = 0
    for item in discovered:
        if item.url in already_seen:
            skipped_seen += 1
            continue
        try:
            candidate = await _fetch_and_ingest(db, source, adapter, item.url, parser_version=f"{source_key}-v1")
            db.commit()
            db.refresh(candidate)
            created.append(candidate)
        except Exception:
            db.rollback()
            errors += 1
            logger.exception("Failed to ingest %s from source %s", item.url, source_key)

    return {
        "discovered": len(discovered),
        "created": len(created),
        "skipped_already_seen": skipped_seen,
        "errors": errors,
        "candidates": created,
    }
