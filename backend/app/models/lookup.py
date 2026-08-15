import datetime as dt

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CrawlPolicy, SourceKind


class Band(Base):
    __tablename__ = "band"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    japanese_name: Mapped[str | None] = mapped_column(String(120))

    characters: Mapped[list["Character"]] = relationship(back_populates="band")


class Character(Base):
    __tablename__ = "character"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    japanese_name: Mapped[str | None] = mapped_column(String(120))
    english_name: Mapped[str | None] = mapped_column(String(120))
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    band_id: Mapped[int | None] = mapped_column(ForeignKey("band.id"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    band: Mapped[Band | None] = relationship(back_populates="characters")


class ItemType(Base):
    __tablename__ = "item_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    label_en: Mapped[str] = mapped_column(String(120))
    label_ja: Mapped[str | None] = mapped_column(String(120))


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[SourceKind] = mapped_column(Enum(SourceKind, name="source_kind"))
    base_url: Mapped[str | None] = mapped_column(String(500))
    trust_priority: Mapped[int] = mapped_column(Integer, default=0)
    crawl_policy: Mapped[CrawlPolicy] = mapped_column(
        Enum(CrawlPolicy, name="crawl_policy"), default=CrawlPolicy.manual_import_only
    )
    robots_checked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
