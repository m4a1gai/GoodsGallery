"""Discovery-only adapter: use a search engine's public results as a way to
find candidate product URLs on sites we don't crawl directly (e.g. because
their own robots.txt/ToS status is unconfirmed). This adapter never fetches
third-party product pages itself in `discover()` — it only returns URLs found
in search results for a human (or a later, confirmed-safe adapter) to follow.

Not wired to a live search API yet — `discover()` raises NotImplementedError
so nothing silently no-ops. Wire this up to a search provider once one is
chosen, keeping the same `search_discovery_only` policy.
"""

from __future__ import annotations

from app.models.enums import CrawlPolicy
from pipeline.sources.base import DiscoveredUrl, DiscoveryParams, FetchResult, NotModified, RawProductDraft


class SearchDiscoveryAdapter:
    source_key = "search_discovery"
    crawl_policy = CrawlPolicy.search_discovery_only

    async def discover(self, params: DiscoveryParams) -> list[DiscoveredUrl]:
        raise NotImplementedError(
            "Wire up a search provider before enabling discovery; "
            "until then, use manual URL import."
        )

    async def fetch(self, url: str, etag: str | None = None) -> FetchResult | type[NotModified]:
        raise NotImplementedError("search_discovery_only sources are not auto-fetched")

    def parse(self, fetch_result: FetchResult) -> RawProductDraft:
        raise NotImplementedError
