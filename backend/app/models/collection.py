import datetime as dt

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CollectionStatus


class UserCollection(Base):
    """Personal ownership state. Deliberately separate from CatalogItem so the
    catalog can be shared/published without leaking personal collection data.
    """

    __tablename__ = "user_collection"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_item.id"), unique=True)
    status: Mapped[CollectionStatus] = mapped_column(
        Enum(CollectionStatus, name="collection_status"), default=CollectionStatus.not_owned
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    purchase_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    purchase_date: Mapped[dt.date | None] = mapped_column(Date)
    purchase_source: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(String(2000))
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    catalog_item: Mapped["CatalogItem"] = relationship()  # noqa: F821
