"""Maps a Source.key to the adapter class that knows how to crawl it.

Only sources with a real, reviewed adapter belong here — a source existing in
the `source` table (for provenance/trust-priority bookkeeping) does not imply
there's crawl code for it yet.
"""

from pipeline.sources.base import SourceAdapter
from pipeline.sources.bushiroad_store import BushiroadStoreAdapter

ADAPTERS: dict[str, type[SourceAdapter]] = {
    "bushiroad_store": BushiroadStoreAdapter,
}
