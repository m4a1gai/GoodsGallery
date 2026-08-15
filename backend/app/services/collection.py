from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalog import CatalogItem
from app.models.collection import UserCollection
from app.models.enums import CollectionStatus
from app.models.lookup import Character


def get_or_create_collection(db: Session, catalog_item_id: int) -> UserCollection:
    row = db.scalar(select(UserCollection).where(UserCollection.catalog_item_id == catalog_item_id))
    if row is None:
        row = UserCollection(catalog_item_id=catalog_item_id, status=CollectionStatus.not_owned, quantity=0)
        db.add(row)
        db.flush()
    return row


def compute_stats(db: Session) -> dict:
    items = list(db.scalars(select(CatalogItem)))
    collections = {c.catalog_item_id: c for c in db.scalars(select(UserCollection))}
    characters = list(db.scalars(select(Character)))

    catalog_total = len(items)
    owned_total = sum(1 for c in collections.values() if c.status == CollectionStatus.owned)
    wishlist_total = sum(1 for c in collections.values() if c.status == CollectionStatus.wishlist)
    total_spent = sum(
        float(c.purchase_price or 0) * max(c.quantity, 1)
        for c in collections.values()
        if c.status == CollectionStatus.owned
    )
    completion_pct = round((owned_total / catalog_total) * 100, 1) if catalog_total else 0.0

    by_character: dict[str, dict[str, int]] = {}
    for ch in characters:
        ch_items = [i for i in items if ch.id in i.character_ids]
        owned = sum(
            1
            for i in ch_items
            if (c := collections.get(i.id)) is not None and c.status == CollectionStatus.owned
        )
        by_character[ch.name] = {"owned": owned, "total": len(ch_items)}

    return {
        "catalog_total": catalog_total,
        "owned_total": owned_total,
        "wishlist_total": wishlist_total,
        "completion_pct": completion_pct,
        "total_spent": total_spent,
        "by_character": by_character,
    }
