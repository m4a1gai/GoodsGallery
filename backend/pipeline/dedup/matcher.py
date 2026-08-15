"""Entity resolution: decide whether a candidate is the same product as an
existing catalog item.

Priority order (highest trust first): product_number exact match > stable
source URL/item-id match > fuzzy name + character/type agreement > image
perceptual hash (auxiliary signal only, never sufficient alone — two
different badges of the same character can look nearly identical).

Confidence bands, mirrored in app/models/enums + the plan:
  >= 0.9  -> auto-merge into the catalog item
  0.6-0.9 -> DuplicateReviewPair, human decides Same/Different
  < 0.6   -> not a duplicate; goes through normal candidate review as a new item
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rapidfuzz import fuzz

AUTO_MERGE_THRESHOLD = 0.9
REVIEW_THRESHOLD = 0.6


@dataclass
class MatchableFields:
    canonical_name: str
    japanese_name: str | None = None
    product_number: str | None = None
    item_type_code: str | None = None
    character_ids: list[int] = field(default_factory=list)
    source_url: str | None = None
    image_phashes: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    catalog_item_id: int
    confidence: float
    reason: str


def _name_similarity(a: MatchableFields, b: MatchableFields) -> float:
    pairs = [
        (a.canonical_name, b.canonical_name),
        (a.japanese_name, b.japanese_name),
    ]
    scores = [fuzz.token_sort_ratio(x, y) / 100 for x, y in pairs if x and y]
    return max(scores) if scores else 0.0


def _image_hash_similarity(a: MatchableFields, b: MatchableFields) -> float:
    if not a.image_phashes or not b.image_phashes:
        return 0.0
    best = 0.0
    for ha in a.image_phashes:
        for hb in b.image_phashes:
            if len(ha) != len(hb):
                continue
            hamming = sum(c1 != c2 for c1, c2 in zip(ha, hb))
            similarity = 1 - (hamming / len(ha))
            best = max(best, similarity)
    return best


def score_pair(candidate: MatchableFields, existing: MatchableFields) -> tuple[float, str]:
    if candidate.product_number and existing.product_number and candidate.product_number == existing.product_number:
        return 0.98, "product_number match"

    if candidate.source_url and candidate.source_url == existing.source_url:
        return 0.95, "identical source URL"

    name_sim = _name_similarity(candidate, existing)
    type_match = bool(candidate.item_type_code) and candidate.item_type_code == existing.item_type_code
    character_overlap = bool(set(candidate.character_ids) & set(existing.character_ids))

    score = name_sim * 0.7
    reasons = [f"name similarity {name_sim:.2f}"]
    if type_match:
        score += 0.15
        reasons.append("item type match")
    if character_overlap:
        score += 0.1
        reasons.append("character overlap")

    image_sim = _image_hash_similarity(candidate, existing)
    if image_sim > 0.85:
        # Auxiliary boost only — never lets a pair reach auto-merge by itself.
        score = min(score + 0.05, REVIEW_THRESHOLD + 0.05)
        reasons.append(f"image hash similarity {image_sim:.2f}")

    return round(min(score, 0.97), 3), ", ".join(reasons)


def find_best_match(candidate: MatchableFields, existing_items: list[tuple[int, MatchableFields]]) -> MatchResult | None:
    best: MatchResult | None = None
    for catalog_item_id, existing in existing_items:
        confidence, reason = score_pair(candidate, existing)
        if best is None or confidence > best.confidence:
            best = MatchResult(catalog_item_id=catalog_item_id, confidence=confidence, reason=reason)
    return best


def classify(confidence: float) -> str:
    if confidence >= AUTO_MERGE_THRESHOLD:
        return "auto_merge"
    if confidence >= REVIEW_THRESHOLD:
        return "review"
    return "not_duplicate"
