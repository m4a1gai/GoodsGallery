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

        title = None
        price = None
        currency = None
        images: list[dict] = []
        metadata: dict = {}

        # 1. JSON-LD structured data (schema.org/Product) is the most reliable signal.
        for node in tree.css('script[type="application/ld+json"]'):
            try:
                data = json.loads(node.text())
            except (json.JSONDecodeError, TypeError):
                continue
            candidates = data if isinstance(data, list) else [data]
            for entry in candidates:
                if not isinstance(entry, dict):
                    continue
                if entry.get("@type") in ("Product", "product"):
                    title = title or entry.get("name")
                    offers = entry.get("offers")
                    if isinstance(offers, dict):
                        price = price or offers.get("price")
                        currency = currency or offers.get("priceCurrency")
                    image = entry.get("image")
                    if isinstance(image, str):
                        images.append({"url": image})
                    elif isinstance(image, list):
                        images.extend({"url": i} for i in image if isinstance(i, str))
                    metadata["json_ld"] = entry

        # 2. OpenGraph fallback.
        if title is None:
            og_title = tree.css_first('meta[property="og:title"]')
            title = og_title.attrs.get("content") if og_title else None
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
            raw_price=float(price) if price not in (None, "") else None,
            raw_currency=currency,
            raw_images=images,
            raw_metadata=metadata,
            raw_html_hash=html_hash,
        )
