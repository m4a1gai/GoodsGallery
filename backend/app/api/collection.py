from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.catalog import CatalogItem
from app.models.collection import UserCollection
from app.models.enums import CollectionStatus
from app.schemas.collection import CollectionStatsOut, UserCollectionOut, UserCollectionUpdateIn
from app.services.collection import compute_stats, get_or_create_collection

router = APIRouter(prefix="/api/collection", tags=["collection"])


@router.get("/items", response_model=list[UserCollectionOut])
def list_collection(
    status: CollectionStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(UserCollection)
    if status is not None:
        stmt = stmt.where(UserCollection.status == status)
    return list(db.scalars(stmt))


@router.get("/stats", response_model=CollectionStatsOut)
def get_stats(db: Session = Depends(get_db)):
    return compute_stats(db)


@router.put("/items/{catalog_item_id}", response_model=UserCollectionOut)
def upsert_collection(catalog_item_id: int, payload: UserCollectionUpdateIn, db: Session = Depends(get_db)):
    if db.get(CatalogItem, catalog_item_id) is None:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    row = get_or_create_collection(db, catalog_item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row
