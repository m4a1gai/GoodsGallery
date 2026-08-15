from pipeline.dedup.matcher import (
    AUTO_MERGE_THRESHOLD,
    REVIEW_THRESHOLD,
    MatchableFields,
    classify,
    find_best_match,
    score_pair,
)


def test_same_product_number_is_auto_merge():
    a = MatchableFields(canonical_name="Kasumi Badge A", product_number="BP-1234")
    b = MatchableFields(canonical_name="戸山香澄 缶バッジ", product_number="BP-1234")
    confidence, reason = score_pair(a, b)
    assert confidence >= AUTO_MERGE_THRESHOLD
    assert "product_number" in reason


def test_similar_name_different_type_stays_below_review():
    a = MatchableFields(canonical_name="Kasumi Acrylic Stand", item_type_code="acrylic_stand", character_ids=[1])
    b = MatchableFields(canonical_name="Kasumi Badge", item_type_code="badge", character_ids=[1])
    confidence, _ = score_pair(a, b)
    assert confidence < REVIEW_THRESHOLD


def test_similar_name_same_type_goes_to_review_not_auto_merge():
    # Same product surfaced by two sources with slightly different title
    # wording/ordering (translation or listing-specific suffixes), no shared
    # product_number or source URL to short-circuit the match.
    a = MatchableFields(
        canonical_name="Toyama Kasumi Can Badge Live Ver.",
        item_type_code="badge",
        character_ids=[1],
    )
    b = MatchableFields(
        canonical_name="Kasumi Can Badge Fes Ver.",
        item_type_code="badge",
        character_ids=[1],
    )
    confidence, _ = score_pair(a, b)
    assert REVIEW_THRESHOLD <= confidence < AUTO_MERGE_THRESHOLD
    assert classify(confidence) == "review"


def test_image_hash_alone_never_reaches_auto_merge():
    same_hash = "f" * 16
    a = MatchableFields(canonical_name="Item A", image_phashes=[same_hash])
    b = MatchableFields(canonical_name="Completely Different Name", image_phashes=[same_hash])
    confidence, _ = score_pair(a, b)
    assert confidence < AUTO_MERGE_THRESHOLD


def test_find_best_match_picks_highest_confidence():
    candidate = MatchableFields(canonical_name="Arisa Badge", product_number="BP-9999")
    existing = [
        (1, MatchableFields(canonical_name="Something Else", product_number="BP-0000")),
        (2, MatchableFields(canonical_name="Arisa Badge Reprint", product_number="BP-9999")),
    ]
    match = find_best_match(candidate, existing)
    assert match is not None
    assert match.catalog_item_id == 2
    assert match.confidence >= AUTO_MERGE_THRESHOLD


def test_no_existing_items_returns_none():
    candidate = MatchableFields(canonical_name="Solo item")
    assert find_best_match(candidate, []) is None
