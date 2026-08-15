"""The only adapter that runs against arbitrary third-party URLs in phase 1.

The user pastes a public product page URL themselves (so there is no automated
discovery/scheduling to worry about), we still check robots.txt before
fetching, then extract JSON-LD / OpenGraph / <title> as a best-effort generic
parser. Site-specific adapters can subclass or replace `parse()` later once a
given source's ToS has been confirmed and its `crawl_policy` is upgraded.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import httpx
from selectolax.parser import HTMLParser

from app.models.enums import CrawlPolicy
from pipeline.http import USER_AGENT, is_allowed_by_robots, polite_get
from pipeline.sources.base import DiscoveredUrl, DiscoveryParams, FetchResult, NotModified, RawProductDraft
from pipeline.sources.common import find_product_ld_json


class ManualImportAdapter:
    source_key = "manual_import"
    crawl_policy = CrawlPolicy.manual_import_only

    async def discover(self, params: DiscoveryParams) -> list[DiscoveredUrl]:
        # No automated discovery: candidate URLs come from the human operator.
        return []

    async def fetch(self, url: str, etag: str | None = None) -> FetchResult | type[NotModified]:
        if not is_allowed_by_robots(url):
            raise PermissionError(f"robots.txt disallows fetching {url}")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await polite_get(client, url)
        if etag and response.headers.get("etag") == etag:
            return NotModified
        response.raise_for_status()
        return FetchResult(
            url=url,
            status_code=response.status_code,
            html=response.text,
            fetched_at=datetime.now(timezone.utc),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )

    def parse(self, fetch_result: FetchResult) -> RawProductDraft:
        tree = HTMLParser(fetch_result.html)

        json_ld_blocks = []
        for node in tree.css('script[type="application/ld+json"]'):
            try:
                json_ld_blocks.append(json.loads(node.text()))
            except (json.JSONDecodeError, TypeError):
                continue

        # 1. JSON-LD structured data (schema.org/Product) is the most reliable signal.
        extracted = find_product_ld_json(json_ld_blocks)
        title = extracted.title if extracted else None
        price = extracted.price if extracted else None
        currency = extracted.currency if extracted else None
        images: list[dict] = [{"url": u} for u in (extracted.images if extracted else [])]
        metadata: dict = {"json_ld": extracted.raw} if extracted else {}
        if extracted and extracted.product_number:
            metadata["product_number"] = extracted.product_number

        # 2. OpenGraph fallback.
        if title is None:
            og_title = tree.css_first('meta[property="og:title"]')
            title = og_title.attrs.get("content") if og_title else None
        if not images:
            og_image = tree.css_first('meta[property="og:image"]')
            if og_image and og_image.attrs.get("content"):
                images.append({"url": og_image.attrs["content"]})

        # 3. <title> as last resort.
        if title is None and tree.css_first("title"):
            title = tree.css_first("title").text(strip=True)

        html_hash = hashlib.sha256(fetch_result.html.encode("utf-8")).hexdigest()

        return RawProductDraft(
            source_url=fetch_result.url,
            raw_title=title,
            raw_price=price,
            raw_currency=currency,
            raw_images=images,
            raw_metadata=metadata,
            raw_html_hash=html_hash,
        )
