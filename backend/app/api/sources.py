from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.enums import CrawlPolicy
from app.models.lookup import Source
from app.schemas.source import CrawlRequestIn, CrawlResultOut, SourceOut
from pipeline.crawl_runner import run_discovery_crawl
from pipeline.sources.base import DiscoveryParams
from pipeline.sources.registry import ADAPTERS

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return list(db.scalars(select(Source).order_by(Source.trust_priority.desc())))


@router.post("/{source_key}/crawl", response_model=CrawlResultOut)
async def crawl_source(source_key: str, payload: CrawlRequestIn, db: Session = Depends(get_db)):
    source = db.scalar(select(Source).where(Source.key == source_key))
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.crawl_policy != CrawlPolicy.auto:
        raise HTTPException(
            status_code=403,
            detail=f"Source crawl_policy is {source.crawl_policy.value!r}, not 'auto'; refusing to bulk-crawl.",
        )
    adapter_cls = ADAPTERS.get(source_key)
    if adapter_cls is None:
        raise HTTPException(status_code=501, detail=f"No adapter implemented for source_key={source_key!r} yet.")

    result = await run_discovery_crawl(
        db,
        source_key,
        adapter_cls(),
        DiscoveryParams(start_url=payload.start_url, max_pages=payload.max_pages),
        limit=payload.limit,
    )
    return CrawlResultOut(
        discovered=result["discovered"],
        created=result["created"],
        skipped_already_seen=result["skipped_already_seen"],
        errors=result["errors"],
        candidate_ids=[c.id for c in result["candidates"]],
    )
