import datetime as dt

from pydantic import BaseModel, ConfigDict


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    japanese_name: str | None
    english_name: str | None
    sort_order: int


class ItemTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    label_en: str
    label_ja: str | None


class CatalogItemImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    source_item_url: str | None
    is_primary: bool


class CatalogItemImageCreateIn(BaseModel):
    image_url: str
    source_item_url: str | None = None
    is_primary: bool = False


class CatalogItemSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    source_url: str
    source_price: float | None
    last_seen_at: dt.datetime | None


class CatalogItemListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    japanese_name: str | None
    character_ids: list[int]
    item_type_id: int | None
    official_price: float | None
    currency: str | None
    data_completeness: float
    primary_image_url: str | None = None


class CatalogItemDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_name: str
    japanese_name: str | None
    original_title: str | None
    translated_title: str | None
    translation_source: str | None
    character_ids: list[int]
    band_id: int | None
    series: str | None
    item_type_id: int | None
    manufacturer: str | None
    release_date: dt.date | None
    release_date_source: str | None
    release_date_confidence: float | None
    official_price: float | None
    currency: str | None
    product_number: str | None
    data_completeness: float
    missing_fields: list[str] = []
    images: list[CatalogItemImageOut] = []
    item_sources: list[CatalogItemSourceOut] = []
