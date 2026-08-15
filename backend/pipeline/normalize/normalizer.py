"""Turn a RawProduct into normalized Candidate fields.

Character matching looks at title/description/metadata against each
Character's name/japanese_name/english_name/aliases — a product doesn't need
the character's name verbatim if e.g. a group-shot alias like "Poppin'Party"
is present, but title-only matching is intentionally conservative: this
assigns character tags and a base confidence, dedup then layers on top.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.lookup import Character
from app.models.pipeline import RawProduct

ITEM_TYPE_KEYWORDS: dict[str, list[str]] = {
    "badge": ["缶バッジ", "badge", "缶バツジ"],
    "acrylic_stand": ["アクリルスタンド", "acrylic stand", "アクスタ"],
    "acrylic_keychain": ["アクリルキーホルダー", "acrylic keychain", "アクキー"],
    "keychain": ["キーホルダー", "keychain"],
    "shikishi": ["色紙", "shikishi"],
    "clear_file": ["クリアファイル", "clear file"],
    "plush": ["ぬいぐるみ", "plush"],
    "figure": ["フィギュア", "figure"],
    "card": ["カード", "card"],
    "bromide": ["ブロマイド", "bromide"],
    "poster": ["ポスター", "poster"],
    "towel": ["タオル", "towel"],
    "clothing": ["Tシャツ", "パーカー", "shirt", "hoodie"],
    "book": ["書籍", "магазин", "magazine", "本"],
}


@dataclass
class NormalizedCandidate:
    canonical_name: str
    japanese_name: str | None
    character_ids: list[int]
    item_type_code: str | None
    product_number: str | None
    base_confidence: float


def match_characters(text: str, characters: list[Character]) -> list[int]:
    matched: list[int] = []
    haystack = text.lower()
    for ch in characters:
        needles = [ch.name, ch.japanese_name, ch.english_name, *ch.aliases]
        for needle in needles:
            if needle and needle.lower() in haystack:
                matched.append(ch.id)
                break
    return matched


def guess_item_type(text: str) -> str | None:
    for code, keywords in ITEM_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                return code
    return None


PRODUCT_NUMBER_RE = re.compile(r"\b([A-Z]{1,4}[-_]?\d{3,8})\b")


def guess_product_number(text: str) -> str | None:
    match = PRODUCT_NUMBER_RE.search(text)
    return match.group(1) if match else None


def normalize(raw: RawProduct, characters: list[Character]) -> NormalizedCandidate:
    text_blob = " ".join(
        filter(
            None,
            [
                raw.raw_title,
                raw.raw_description,
                raw.source_url,
                str(raw.raw_metadata.get("json_ld", "")) if raw.raw_metadata else "",
            ],
        )
    )

    character_ids = match_characters(text_blob, characters)
    item_type_code = guess_item_type(text_blob)
    product_number = guess_product_number(text_blob)

    # Confidence is deliberately conservative here: it only reflects how much
    # signal normalization found, not whether this is a *new* item — dedup
    # layers identity confidence on top of this.
    signals_found = sum([bool(character_ids), bool(item_type_code), bool(raw.raw_title)])
    base_confidence = round(0.3 + 0.2 * signals_found, 2)

    return NormalizedCandidate(
        canonical_name=raw.raw_title or "Unknown item",
        japanese_name=raw.raw_title if raw.raw_title and re.search(r"[぀-ヿ一-鿿]", raw.raw_title) else None,
        character_ids=character_ids,
        item_type_code=item_type_code,
        product_number=product_number,
        base_confidence=min(base_confidence, 0.6),  # normalization alone never reaches "high confidence"
    )
