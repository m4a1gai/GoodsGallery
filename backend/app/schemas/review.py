import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.models.enums import CandidateStatus, DuplicateReviewStatus


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    raw_product_id: int
    canonical_name: str
    japanese_name: str | None
    character_ids: list[int]
    series: str | None
    item_type_id: int | None
    manufacturer: str | None
    price: float | None
    currency: str | None
    product_number: str | None
    images: list
    confidence: float
    status: CandidateStatus
    created_at: dt.datetime
    source_url: str | None = None


class CandidateEditIn(BaseModel):
    canonical_name: str | None = None
    japanese_name: str | None = None
    character_ids: list[int] | None = None
    series: str | None = None
    item_type_id: int | None = None
    manufacturer: str | None = None
    product_number: str | None = None
    images: list[dict] | None = None


class SplitItemIn(BaseModel):
    canonical_name: str
    japanese_name: str | None = None
    image_url: str


class SplitRequestIn(BaseModel):
    splits: list[SplitItemIn]


class DuplicateReviewPairOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    matched_catalog_item_id: int
    similarity_score: float
    match_reason: str | None
    status: DuplicateReviewStatus
