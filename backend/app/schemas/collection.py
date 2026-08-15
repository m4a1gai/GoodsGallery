import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.models.enums import CollectionStatus


class UserCollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_item_id: int
    status: CollectionStatus
    quantity: int
    purchase_price: float | None
    currency: str | None
    purchase_date: dt.date | None
    purchase_source: str | None
    notes: str | None


class UserCollectionUpdateIn(BaseModel):
    status: CollectionStatus | None = None
    quantity: int | None = None
    purchase_price: float | None = None
    currency: str | None = None
    purchase_date: dt.date | None = None
    purchase_source: str | None = None
    notes: str | None = None


class CollectionStatsOut(BaseModel):
    catalog_total: int
    owned_total: int
    wishlist_total: int
    completion_pct: float
    total_spent: float
    by_character: dict[str, dict[str, int]]
