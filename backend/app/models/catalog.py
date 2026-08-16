import datetime as dt

from sqlalchemy import ARRAY, Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class CatalogItem(Base):
    __tablename__ = "catalog_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    canonical_name: Mapped[str] = mapped_column(String(300))
    japanese_name: Mapped[str | None] = mapped_column(String(300))
    original_title: Mapped[str | None] = mapped_column(String(500))
    translated_title: Mapped[str | None] = mapped_column(String(500))
    translation_source: Mapped[str | None] = mapped_column(String(60))

    character_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    band_id: Mapped[int | None] = mapped_column(ForeignKey("band.id"))
    series: Mapped[str | None] = mapped_column(String(300))
    item_type_id: Mapped[int | None] = mapped_column(ForeignKey("item_type.id"))
    manufacturer: Mapped[str | None] = mapped_column(String(200))

    release_date: Mapped[dt.date | None] = mapped_column(Date)
    release_date_source: Mapped[str | None] = mapped_column(String(120))
    release_date_confidence: Mapped[float | None] = mapped_column(Float)

    official_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    product_number: Mapped[str | None] = mapped_column(String(120))

    data_completeness: Mapped[float] = mapped_column(Float, default=0.0)

    created_by: Mapped[str] = mapped_column(String(30), default="manual")
    updated_by: Mapped[str] = mapped_column(String(30), default="manual")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    images: Mapped[list["CatalogItemImage"]] = relationship(back_populates="catalog_item", cascade="all, delete-orphan")
    item_sources: Mapped[list["CatalogItemSource"]] = relationship(
        back_populates="catalog_item", cascade="all, delete-orphan"
    )
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="catalog_item", cascade="all, delete-orphan")


class CatalogItemImage(Base):
    __tablename__ = "catalog_item_image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_item.id"))
    # Text, not String(N): a cropped image is stored as a base64 data: URI
    # here (see pipeline images strategy in README), which can run to tens
    # of KB — nowhere near a normal URL's length.
    image_url: Mapped[str] = mapped_column(Text)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source.id"))
    source_item_url: Mapped[str | None] = mapped_column(String(1000))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    catalog_item: Mapped[CatalogItem] = relationship(back_populates="images")


class CatalogItemSource(Base):
    __tablename__ = "catalog_item_source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_item.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    source_url: Mapped[str] = mapped_column(String(1000))
    source_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    last_seen_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    catalog_item: Mapped[CatalogItem] = relationship(back_populates="item_sources")
    source: Mapped["Source"] = relationship()  # noqa: F821


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_item.id"))
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source.id"))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="JPY")
    observed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    catalog_item: Mapped[CatalogItem] = relationship(back_populates="price_history")
