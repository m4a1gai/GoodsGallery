"""Source Adapter contract.

Every data source (official site, retailer, secondhand shop, search-engine
discovery, or manual paste) implements this Protocol. `crawl_runner` inspects
`crawl_policy` before scheduling anything automatically — adapters marked
`manual_import_only` or `disabled` can only be invoked by a human pasting a URL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.models.enums import CrawlPolicy


@dataclass
class DiscoveryParams:
    keyword: str | None = None
    character_key: str | None = None
    item_type_code: str | None = None
    max_pages: int = 5


@dataclass
class DiscoveredUrl:
    url: str
    reason: str  # e.g. "search result", "sitemap", "manual paste"


@dataclass
class FetchResult:
    url: str
    status_code: int
    html: str
    fetched_at: datetime
    etag: str | None = None
    last_modified: str | None = None


class NotModified:
    """Sentinel returned by fetch() when the server confirms no change (304 / matching etag)."""


@dataclass
class RawProductDraft:
    source_url: str
    raw_title: str | None
    raw_description: str | None = None
    raw_price: float | None = None
    raw_currency: str | None = None
    raw_images: list[dict] = field(default_factory=list)
    raw_metadata: dict = field(default_factory=dict)
    raw_html_hash: str | None = None


class SourceAdapter(Protocol):
    source_key: str
    crawl_policy: CrawlPolicy

    async def discover(self, params: DiscoveryParams) -> list[DiscoveredUrl]:
        """Find candidate product URLs. May hit a search engine or a site's own
        search/listing pages, subject to crawl_policy and robots.txt."""
        ...

    async def fetch(self, url: str, etag: str | None = None) -> FetchResult | type[NotModified]:
        """Fetch a single URL, honoring conditional-GET headers when available."""
        ...

    def parse(self, fetch_result: FetchResult) -> RawProductDraft:
        """Extract raw product fields from a fetched page. No normalization here —
        that happens later in pipeline/normalize."""
        ...
