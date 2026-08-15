from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem, CatalogItemImage

REQUIRED_FIELDS = [
    "japanese_name",
    "series",
    "item_type_id",
    "manufacturer",
    "release_date",
    "official_price",
    "product_number",
]

FIELD_LABELS = {
    "japanese_name": "Japanese name",
    "series": "Series",
    "item_type_id": "Item type",
    "manufacturer": "Manufacturer",
    "release_date": "Release date",
    "official_price": "Official price",
    "product_number": "Product number",
}


def compute_completeness(item: CatalogItem) -> tuple[float, list[str]]:
    missing = [f for f in REQUIRED_FIELDS if getattr(item, f) in (None, "")]
    if not item.images:
        missing.append("images")
    total_fields = len(REQUIRED_FIELDS) + 1
    filled = total_fields - len(missing)
    completeness = round(filled / total_fields, 4)
    missing_labels = [FIELD_LABELS.get(f, f) for f in missing if f != "images"]
    if "images" in missing:
        missing_labels.append("Images")
    return completeness, missing_labels


def list_catalog_items(
    db: Session,
    *,
    character_id: int | None = None,
    character_mode: str = "includes",  # "includes" | "exact"
    item_type_id: int | None = None,
    search: str | None = None,
    limit: int = 60,
    offset: int = 0,
) -> list[CatalogItem]:
    stmt = select(CatalogItem)

    if character_id is not None:
        if character_mode == "exact":
            stmt = stmt.where(CatalogItem.character_ids == [character_id])
        else:
            stmt = stmt.where(CatalogItem.character_ids.any(character_id))

    if item_type_id is not None:
        stmt = stmt.where(CatalogItem.item_type_id == item_type_id)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                CatalogItem.canonical_name.ilike(pattern),
                CatalogItem.japanese_name.ilike(pattern),
                CatalogItem.series.ilike(pattern),
            )
        )

    stmt = stmt.order_by(CatalogItem.release_date.desc().nullslast(), CatalogItem.id.desc())
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).unique())


def get_primary_image_url(item: CatalogItem) -> str | None:
    for image in item.images:
        if image.is_primary:
            return image.image_url
    return item.images[0].image_url if item.images else None
