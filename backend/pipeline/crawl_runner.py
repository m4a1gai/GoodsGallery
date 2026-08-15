"""Orchestrates one pipeline run: fetch -> RawProduct -> normalize -> Candidate
-> dedup against the existing catalog.

Phase 1 only drives this with ManualImportAdapter (a human-supplied URL), so
there is no scheduler here yet — `run_manual_import` is called directly (e.g.
from a CLI script or a future admin-triggered API call). Adapters with
crawl_policy != manual_import_only are intentionally not invoked by anything
in this module yet; wiring up scheduled `auto` crawling is a P1/P2 follow-up
once a given source's ToS has been confirmed.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem
from app.models.lookup import Character, ItemType, Source
from app.models.pipeline import Candidate, DuplicateReviewPair, RawProduct
from pipeline.dedup.matcher import (
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
    MatchableFields,
    find_best_match,
)
from pipeline.normalize.normalizer import normalize
from pipeline.sources.base import FetchResult, NotModified
from pipeline.sources.manual_import import ManualImportAdapter


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


async def run_manual_import(db: Session, source_key: str, url: str) -> Candidate:
    source = db.scalar(select(Source).where(Source.key == source_key))
    if source is None:
        raise ValueError(f"Unknown source key: {source_key}")

    adapter = ManualImportAdapter()
    fetch_result = await adapter.fetch(url)
    if fetch_result is NotModified:
        raise RuntimeError("Page reported not modified on first fetch; unexpected")
    assert isinstance(fetch_result, FetchResult)

    draft = adapter.parse(fetch_result)

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
        parser_version="manual_import-v1",
    )
    db.add(raw)
    db.flush()

    characters = list(db.scalars(select(Character)))
    normalized = normalize(raw, characters)
    item_type = db.scalar(select(ItemType).where(ItemType.code == normalized.item_type_code)) if normalized.item_type_code else None

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

    db.commit()
    db.refresh(candidate)
    return candidate
