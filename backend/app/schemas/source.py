import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.models.enums import CrawlPolicy, SourceKind


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    kind: SourceKind
    base_url: str | None
    trust_priority: int
    crawl_policy: CrawlPolicy
    robots_checked_at: dt.datetime | None
    notes: str | None


class CrawlRequestIn(BaseModel):
    start_url: str
    max_pages: int = 3
    limit: int | None = None


class CrawlResultOut(BaseModel):
    discovered: int
    created: int
    skipped_already_seen: int
    errors: int
    candidate_ids: list[int]
