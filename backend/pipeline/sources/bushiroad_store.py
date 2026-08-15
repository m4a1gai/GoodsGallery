"""Adapter for bushiroad-store.com — Bushiroad's own first-party goods store
(Shopify-based). This is the first source in the project upgraded past
manual_import_only to `auto`, on the basis of an actual check rather than a
default:

  - robots.txt (checked 2026-08-15): `/collections/` and `/products/` are not
    disallowed for a generic User-agent; only specific query-string variants
    (sort_by, filter combos — infinite-crawl traps) are blocked. A sitemap is
    published at /sitemap.xml.
  - Terms of Service (checked 2026-08-15): no clause restricting automated
    access/scraping.
  - It's the manufacturer's own storefront, i.e. the highest-trust `official`
    source kind in this project, not a marketplace/reseller.

`discover()` still only fetches what a human points it at (a collection URL,
e.g. https://bushiroad-store.com/collections/kasumi) — there is no
site-wide/keyword-free crawl and no background scheduler anywhere in this
codebase. "auto" here means the adapter *can* walk a listing's pagination and
fetch every product on it in one run, not that anything runs unattended.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import httpx
from selectolax.parser import HTMLParser

from app.models.enums import CrawlPolicy
from pipeline.http import is_allowed_by_robots, polite_get
from pipeline.sources.base import DiscoveredUrl, DiscoveryParams, FetchResult, NotModified, RawProductDraft
from pipeline.sources.common import find_product_ld_json

BASE_URL = "https://bushiroad-store.com"


class BushiroadStoreAdapter:
    source_key = "bushiroad_store"
    crawl_policy = CrawlPolicy.auto

    async def discover(self, params: DiscoveryParams) -> list[DiscoveredUrl]:
        if not params.start_url:
            raise ValueError("BushiroadStoreAdapter.discover requires DiscoveryParams.start_url (a collection page)")
        if urlparse(params.start_url).netloc != urlparse(BASE_URL).netloc:
            raise ValueError(f"start_url must be on {BASE_URL}")

        found: dict[str, DiscoveredUrl] = {}
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for page in range(1, params.max_pages + 1):
                page_url = params.start_url if page == 1 else f"{params.start_url}?page={page}"
                if not is_allowed_by_robots(page_url):
                    break
                response = await polite_get(client, page_url)
                if response.status_code != 200:
                    break
                tree = HTMLParser(response.text)
                links = [
                    urljoin(BASE_URL, a.attrs["href"])
                    for a in tree.css("a[href]")
                    if "/products/" in a.attrs.get("href", "")
                ]
                new_links = [link.split("?")[0] for link in links if link.split("?")[0] not in found]
                if not new_links:
                    break
                for link in new_links:
                    found[link] = DiscoveredUrl(url=link, reason=f"collection page {page_url}")

        return list(found.values())

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

        extracted = find_product_ld_json(json_ld_blocks)

        title = extracted.title if extracted else None
        images: list[dict] = [{"url": u} for u in (extracted.images if extracted else [])]
        metadata: dict = {"json_ld": extracted.raw} if extracted else {}
        if extracted and extracted.product_number:
            metadata["product_number"] = extracted.product_number

        if title is None:
            og_title = tree.css_first('meta[property="og:title"]')
            title = og_title.attrs.get("content") if og_title else None
        if not images:
            og_image = tree.css_first('meta[property="og:image"]')
            if og_image and og_image.attrs.get("content"):
                images.append({"url": og_image.attrs["content"]})

        html_hash = hashlib.sha256(fetch_result.html.encode("utf-8")).hexdigest()

        return RawProductDraft(
            source_url=fetch_result.url,
            raw_title=title,
            raw_price=extracted.price if extracted else None,
            raw_currency=extracted.currency if extracted else None,
            raw_images=images,
            raw_metadata=metadata,
            raw_html_hash=html_hash,
        )
