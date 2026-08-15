from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.catalog import CatalogItem
from app.models.enums import CandidateStatus
from app.models.pipeline import Candidate, DuplicateReviewPair
from app.schemas.review import CandidateEditIn, CandidateOut, DuplicateReviewPairOut
from app.services.review import accept_candidate, reject_candidate, resolve_duplicate_pair

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/candidates", response_model=list[CandidateOut])
def list_candidates(
    status: CandidateStatus = Query(default=CandidateStatus.pending),
    db: Session = Depends(get_db),
):
    stmt = select(Candidate).where(Candidate.status == status).order_by(Candidate.confidence.desc())
    return list(db.scalars(stmt))


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


class RejectIn(BaseModel):
    reason: str | None = None


@router.post("/candidates/{candidate_id}/accept", response_model=CandidateOut)
def accept(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if candidate.status != CandidateStatus.pending:
        raise HTTPException(status_code=400, detail="Candidate already reviewed")
    accept_candidate(db, candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("/candidates/{candidate_id}/reject", response_model=CandidateOut)
def reject(candidate_id: int, payload: RejectIn, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    reject_candidate(db, candidate, payload.reason)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def edit(candidate_id: int, payload: CandidateEditIn, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    return candidate


class MergeIn(BaseModel):
    catalog_item_id: int


@router.post("/candidates/{candidate_id}/merge", response_model=CandidateOut)
def merge(candidate_id: int, payload: MergeIn, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    catalog_item = db.get(CatalogItem, payload.catalog_item_id)
    if catalog_item is None:
        raise HTTPException(status_code=404, detail="Catalog item not found")
    from app.services.review import merge_candidate

    merge_candidate(db, candidate, catalog_item)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/duplicates", response_model=list[DuplicateReviewPairOut])
def list_duplicates(db: Session = Depends(get_db)):
    from app.models.enums import DuplicateReviewStatus

    stmt = select(DuplicateReviewPair).where(DuplicateReviewPair.status == DuplicateReviewStatus.pending)
    return list(db.scalars(stmt))


class DuplicateResolveIn(BaseModel):
    is_same: bool


@router.post("/duplicates/{pair_id}/resolve")
def resolve_duplicate(pair_id: int, payload: DuplicateResolveIn, db: Session = Depends(get_db)):
    pair = db.get(DuplicateReviewPair, pair_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="Duplicate pair not found")
    resolve_duplicate_pair(db, pair, payload.is_same)
    db.commit()
    return {"ok": True}
