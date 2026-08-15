"""CLI: bulk-import every product listed on a collection/category page.

Only works for a source whose crawl_policy is `auto` in the database — see
pipeline/crawl_runner.run_discovery_crawl. This is still a single, human-
triggered run (not a scheduled job): you decide which collection page to
point it at and when to run it.

Usage:
    python -m scripts.crawl_collection bushiroad_store \
        "https://bushiroad-store.com/collections/kasumi" --max-pages 3 --limit 20
"""

import argparse
import asyncio

from app.core.db import SessionLocal
from pipeline.crawl_runner import run_discovery_crawl
from pipeline.sources.base import DiscoveryParams
from pipeline.sources.registry import ADAPTERS


async def main(source_key: str, start_url: str, max_pages: int, limit: int | None) -> None:
    adapter_cls = ADAPTERS.get(source_key)
    if adapter_cls is None:
        raise SystemExit(f"No adapter registered for source_key={source_key!r}. Known: {list(ADAPTERS)}")

    db = SessionLocal()
    try:
        result = await run_discovery_crawl(
            db,
            source_key,
            adapter_cls(),
            DiscoveryParams(start_url=start_url, max_pages=max_pages),
            limit=limit,
        )
        print(
            f"Discovered {result['discovered']} product URLs: "
            f"{result['created']} new candidates created, "
            f"{result['skipped_already_seen']} already seen, "
            f"{result['errors']} errors."
        )
        for c in result["candidates"]:
            print(f"  candidate #{c.id}: {c.canonical_name!r} (confidence={c.confidence})")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_key")
    parser.add_argument("start_url")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    asyncio.run(main(args.source_key, args.start_url, args.max_pages, args.limit))
