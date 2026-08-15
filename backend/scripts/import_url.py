"""CLI: manually import one product URL through the pipeline.

Usage:
    python -m scripts.import_url <source_key> <url>

The source must already exist in the `source` table with crawl_policy allowing
manual import (manual_import_only or search_discovery_only sources still
require a human to supply the URL here — nothing auto-schedules this).
"""

import asyncio
import sys

from app.core.db import SessionLocal
from pipeline.crawl_runner import run_manual_import


async def main(source_key: str, url: str) -> None:
    db = SessionLocal()
    try:
        candidate = await run_manual_import(db, source_key, url)
        print(f"Created candidate #{candidate.id}: {candidate.canonical_name!r} (confidence={candidate.confidence})")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
