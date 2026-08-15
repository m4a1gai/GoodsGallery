import datetime as dt

from sqlalchemy import ARRAY, Date, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import CandidateStatus, DuplicateReviewStatus


class RawProduct(Base):
    """Immutable, append-only snapshot of what a source adapter fetched.

    Never overwritten so that a normalizer bump can be replayed against history.
    """

    __tablename__ = "raw_product"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    source_url: Mapped[str] = mapped_column(String(1000))
    crawled_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_title: Mapped[str | None] = mapped_column(String(500))
    raw_description: Mapped[str | None] = mapped_column(String)
    raw_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    raw_currency: Mapped[str | None] = mapped_column(String(10))
    raw_images: Mapped[list] = mapped_column(JSONB, default=list)
    raw_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    raw_html_hash: Mapped[str | None] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(30))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    etag: Mapped[str | None] = mapped_column(String(200))
    last_modified: Mapped[str | None] = mapped_column(String(120))

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="raw_product")


class Candidate(Base):
    """Normalized, deduplication-scored product waiting for catalog admission."""

    __tablename__ = "candidate"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_product_id: Mapped[int] = mapped_column(ForeignKey("raw_product.id"))

    canonical_name: Mapped[str] = mapped_column(String(300))
    japanese_name: Mapped[str | None] = mapped_column(String(300))
    character_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    series: Mapped[str | None] = mapped_column(String(300))
    item_type_id: Mapped[int | None] = mapped_column(ForeignKey("item_type.id"))
    manufacturer: Mapped[str | None] = mapped_column(String(200))
    release_date: Mapped[dt.date | None] = mapped_column(Date)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    product_number: Mapped[str | None] = mapped_column(String(120))
    images: Mapped[list] = mapped_column(JSONB, default=list)

    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, name="candidate_status"), default=CandidateStatus.pending
    )
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(String(1000))
    accepted_catalog_item_id: Mapped[int | None] = mapped_column(ForeignKey("catalog_item.id"))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_product: Mapped[RawProduct] = relationship(back_populates="candidates")

    @property
    def source_url(self) -> str | None:
        return self.raw_product.source_url if self.raw_product else None


class DuplicateReviewPair(Base):
    """A candidate that looks like it might already exist in the catalog (medium confidence)."""

    __tablename__ = "duplicate_review_pair"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidate.id"))
    matched_catalog_item_id: Mapped[int] = mapped_column(ForeignKey("catalog_item.id"))
    similarity_score: Mapped[float] = mapped_column(Float)
    match_reason: Mapped[str | None] = mapped_column(String(300))
    status: Mapped[DuplicateReviewStatus] = mapped_column(
        Enum(DuplicateReviewStatus, name="duplicate_review_status"), default=DuplicateReviewStatus.pending
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
