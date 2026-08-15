"""Shared, polite HTTP client for source adapters.

Enforces: bounded concurrency, a minimum delay between requests to the same
host, exponential backoff on 429/5xx, and a request timeout. Adapters must
call `is_allowed_by_robots()` before fetching a new host and skip it (falling
back to manual import) if disallowed.
"""

from __future__ import annotations

import asyncio
import time
import urllib.robotparser
from urllib.parse import urlparse

import httpx

USER_AGENT = "GoodsGalleryBot/0.1 (+personal catalog project; contact: gunlin.m4a1gai@gmail.com)"

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}
_last_request_at: dict[str, float] = {}

MIN_DELAY_SECONDS = 3.0
MAX_RETRIES = 3


def is_allowed_by_robots(url: str) -> bool:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    parser = _robots_cache.get(origin)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(f"{origin}/robots.txt")
        try:
            parser.read()
        except OSError:
            # robots.txt unreachable: fail closed, do not assume allowed.
            return False
        _robots_cache[origin] = parser
    return parser.can_fetch(USER_AGENT, url)


async def _respect_rate_limit(host: str) -> None:
    last = _last_request_at.get(host)
    if last is not None:
        elapsed = time.monotonic() - last
        if elapsed < MIN_DELAY_SECONDS:
            await asyncio.sleep(MIN_DELAY_SECONDS - elapsed)
    _last_request_at[host] = time.monotonic()


async def polite_get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    if not is_allowed_by_robots(url):
        raise PermissionError(f"robots.txt disallows fetching {url}")

    host = urlparse(url).netloc
    delay = MIN_DELAY_SECONDS
    for attempt in range(1, MAX_RETRIES + 1):
        await _respect_rate_limit(host)
        response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=15.0)
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == MAX_RETRIES:
                response.raise_for_status()
            await asyncio.sleep(delay)
            delay *= 2
            continue
        return response
    raise RuntimeError("unreachable")
