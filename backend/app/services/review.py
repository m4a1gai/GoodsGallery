import datetime as dt

from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem, CatalogItemImage, CatalogItemSource
from app.models.enums import CandidateStatus, DuplicateReviewStatus
from app.models.pipeline import Candidate, DuplicateReviewPair, RawProduct


def _add_images_and_source(db: Session, catalog_item: CatalogItem, candidate: Candidate, raw: RawProduct) -> None:
    existing_urls = {img.image_url for img in catalog_item.images}
    for image in candidate.images or []:
        url = image.get("url") if isinstance(image, dict) else None
        if url and url not in existing_urls:
            db.add(
                CatalogItemImage(
                    catalog_item_id=catalog_item.id,
                    image_url=url,
                    source_id=raw.source_id,
                    source_item_url=raw.source_url,
                    is_primary=not catalog_item.images,
                )
            )

    already_linked = any(s.source_id == raw.source_id and s.source_url == raw.source_url for s in catalog_item.item_sources)
    if not already_linked:
        db.add(
            CatalogItemSource(
                catalog_item_id=catalog_item.id,
                source_id=raw.source_id,
                source_url=raw.source_url,
                source_price=candidate.price,
                last_seen_at=dt.datetime.now(dt.timezone.utc),
            )
        )


def accept_candidate(db: Session, candidate: Candidate) -> CatalogItem:
    raw = candidate.raw_product
    catalog_item = CatalogItem(
        canonical_name=candidate.canonical_name,
        japanese_name=candidate.japanese_name,
        original_title=raw.raw_title,
        character_ids=candidate.character_ids,
        series=candidate.series,
        item_type_id=candidate.item_type_id,
        manufacturer=candidate.manufacturer,
        release_date=candidate.release_date,
        official_price=candidate.price,
        currency=candidate.currency,
        product_number=candidate.product_number,
        created_by="crawler",
        updated_by="crawler",
    )
    db.add(catalog_item)
    db.flush()

    _add_images_and_source(db, catalog_item, candidate, raw)

    candidate.status = CandidateStatus.accepted
    candidate.reviewed_at = dt.datetime.now(dt.timezone.utc)
    candidate.accepted_catalog_item_id = catalog_item.id
    return catalog_item


def merge_candidate(db: Session, candidate: Candidate, catalog_item: CatalogItem) -> CatalogItem:
    raw = candidate.raw_product
    _add_images_and_source(db, catalog_item, candidate, raw)

    candidate.status = CandidateStatus.merged
    candidate.reviewed_at = dt.datetime.now(dt.timezone.utc)
    candidate.accepted_catalog_item_id = catalog_item.id
    return catalog_item


def reject_candidate(db: Session, candidate: Candidate, reason: str | None) -> None:
    candidate.status = CandidateStatus.rejected
    candidate.reviewed_at = dt.datetime.now(dt.timezone.utc)
    candidate.review_note = reason


def resolve_duplicate_pair(db: Session, pair: DuplicateReviewPair, is_same: bool) -> CatalogItem | None:
    candidate = db.get(Candidate, pair.candidate_id)
    if is_same:
        catalog_item = db.get(CatalogItem, pair.matched_catalog_item_id)
        merge_candidate(db, candidate, catalog_item)
        pair.status = DuplicateReviewStatus.same
        return catalog_item
    else:
        pair.status = DuplicateReviewStatus.different
        return None
