from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.catalog import CatalogItem
from app.schemas.catalog import CatalogItemDetailOut, CatalogItemListOut, CharacterOut, ItemTypeOut
from app.services.catalog import compute_completeness, get_primary_image_url, list_catalog_items

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("/items", response_model=list[CatalogItemListOut])
def get_catalog_items(
    character_id: int | None = Query(default=None),
    character_mode: str = Query(default="includes", pattern="^(includes|exact)$"),
    item_type_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=60, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    items = list_catalog_items(
        db,
        character_id=character_id,
        character_mode=character_mode,
        item_type_id=item_type_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    out = []
    for item in items:
        completeness, _ = compute_completeness(item)
        out.append(
            CatalogItemListOut(
                id=item.id,
                canonical_name=item.canonical_name,
                japanese_name=item.japanese_name,
                character_ids=item.character_ids,
                item_type_id=item.item_type_id,
                official_price=float(item.official_price) if item.official_price is not None else None,
                currency=item.currency,
                data_completeness=completeness,
                primary_image_url=get_primary_image_url(item),
            )
        )
    return out


@router.get("/items/{item_id}", response_model=CatalogItemDetailOut)
def get_catalog_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(CatalogItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    completeness, missing = compute_completeness(item)
    return CatalogItemDetailOut(
        id=item.id,
        canonical_name=item.canonical_name,
        japanese_name=item.japanese_name,
        original_title=item.original_title,
        translated_title=item.translated_title,
        translation_source=item.translation_source,
        character_ids=item.character_ids,
        band_id=item.band_id,
        series=item.series,
        item_type_id=item.item_type_id,
        manufacturer=item.manufacturer,
        release_date=item.release_date,
        release_date_source=item.release_date_source,
        release_date_confidence=item.release_date_confidence,
        official_price=float(item.official_price) if item.official_price is not None else None,
        currency=item.currency,
        product_number=item.product_number,
        data_completeness=completeness,
        missing_fields=missing,
        images=item.images,
        item_sources=item.item_sources,
    )


@router.get("/characters", response_model=list[CharacterOut])
def get_characters(db: Session = Depends(get_db)):
    from app.models.lookup import Character

    return list(db.query(Character).order_by(Character.sort_order).all())


@router.get("/item-types", response_model=list[ItemTypeOut])
def get_item_types(db: Session = Depends(get_db)):
    from app.models.lookup import ItemType

    return list(db.query(ItemType).order_by(ItemType.label_en).all())
