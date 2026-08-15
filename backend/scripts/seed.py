"""Populate the database with a small hand-picked mock dataset so the UI can
be exercised before any real crawler adapter is turned on.

Not sourced from real crawling: every image URL is a placeholder. This is
explicitly seed/demo data, not catalog data claiming to represent real
products — see the project plan's "P0 skeleton, mock data first" phase.

Usage:
    python -m scripts.seed
"""

import base64
import datetime as dt
import hashlib
from xml.sax.saxutils import escape

from app.core.db import Base, SessionLocal, engine
from app.models.catalog import CatalogItem, CatalogItemImage
from app.models.collection import UserCollection
from app.models.enums import CandidateStatus, CollectionStatus, CrawlPolicy, SourceKind
from app.models.lookup import Band, Character, ItemType, Source
from app.models.pipeline import Candidate, RawProduct

PALETTE = ["#ff6fa5", "#4c8bf5", "#f5a623", "#59c78a", "#a374db", "#e0607a"]


def placeholder_data_uri(label: str) -> str:
    """Self-contained inline-SVG placeholder image (no external network call,
    so it always renders regardless of ad blockers / offline dev / CDN
    hiccups). Only used for seed/mock data — real catalog images come from
    CatalogItemImage.image_url pointing at an actual source once the pipeline
    ingests real products.
    """
    color = PALETTE[int(hashlib.sha256(label.encode()).hexdigest(), 16) % len(PALETTE)]

    words = label.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > 14 and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    lines = lines[:4]

    line_height = 26
    start_y = 200 - (len(lines) - 1) * line_height / 2
    text_spans = "".join(
        f'<tspan x="200" y="{start_y + i * line_height:.0f}">{escape(line)}</tspan>' for i, line in enumerate(lines)
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">'
        f'<rect width="400" height="400" fill="{color}"/>'
        f'<text font-family="sans-serif" font-size="22" fill="white" text-anchor="middle">{text_spans}</text>'
        f"</svg>"
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def run() -> None:
    Base.metadata.create_all(engine)  # no-op if Alembic already created tables; safe for fresh dev DBs too
    db = SessionLocal()
    try:
        if db.query(Band).count() > 0:
            print("Seed data already present, skipping.")
            return

        band = Band(name="Poppin'Party", japanese_name="ポピパ")
        db.add(band)
        db.flush()

        characters = [
            Character(name="Kasumi Toyama", japanese_name="戸山香澄", english_name="Kasumi Toyama",
                       aliases=["Toyama Kasumi", "香澄", "Kasumi"], band_id=band.id, sort_order=1),
            Character(name="Arisa Ichigaya", japanese_name="市ヶ谷有咲", english_name="Arisa Ichigaya",
                       aliases=["Ichigaya Arisa", "有咲", "Arisa"], band_id=band.id, sort_order=2),
            Character(name="Tae Hanazono", japanese_name="花園たえ", english_name="Tae Hanazono",
                       aliases=["Hanazono Tae"], band_id=band.id, sort_order=3),
            Character(name="Rimi Ushigome", japanese_name="牛込里美", english_name="Rimi Ushigome",
                       aliases=["Ushigome Rimi"], band_id=band.id, sort_order=4),
            Character(name="Saaya Yamabuki", japanese_name="山吹沙綾", english_name="Saaya Yamabuki",
                       aliases=["Yamabuki Saaya"], band_id=band.id, sort_order=5),
        ]
        db.add_all(characters)
        db.flush()
        kasumi, arisa, tae, rimi, saaya = characters

        item_types = [
            ItemType(code="badge", label_en="Badge", label_ja="缶バッジ"),
            ItemType(code="acrylic_stand", label_en="Acrylic Stand", label_ja="アクリルスタンド"),
            ItemType(code="acrylic_keychain", label_en="Acrylic Keychain", label_ja="アクリルキーホルダー"),
            ItemType(code="keychain", label_en="Keychain", label_ja="キーホルダー"),
            ItemType(code="shikishi", label_en="Shikishi", label_ja="色紙"),
            ItemType(code="clear_file", label_en="Clear File", label_ja="クリアファイル"),
            ItemType(code="plush", label_en="Plush", label_ja="ぬいぐるみ"),
            ItemType(code="figure", label_en="Figure", label_ja="フィギュア"),
            ItemType(code="card", label_en="Card", label_ja="カード"),
            ItemType(code="bromide", label_en="Bromide", label_ja="ブロマイド"),
            ItemType(code="poster", label_en="Poster", label_ja="ポスター"),
            ItemType(code="towel", label_en="Towel", label_ja="タオル"),
            ItemType(code="clothing", label_en="Clothing", label_ja="衣類"),
            ItemType(code="book", label_en="Book / Magazine", label_ja="書籍"),
            ItemType(code="other", label_en="Other", label_ja="その他"),
        ]
        db.add_all(item_types)
        db.flush()
        badge, acrylic_stand, acrylic_keychain = item_types[0], item_types[1], item_types[2]

        sources = [
            Source(key="manual_import", name="Manual URL Import", kind=SourceKind.user_submitted,
                   crawl_policy=CrawlPolicy.manual_import_only,
                   notes="Human pastes a public product URL; only automated fetch path enabled in phase 1."),
            Source(key="bushiroad_store", name="Bushiroad Store", kind=SourceKind.official,
                   base_url="https://bushiroad-store.com", trust_priority=90,
                   crawl_policy=CrawlPolicy.auto,
                   robots_checked_at=dt.datetime.now(dt.timezone.utc),
                   notes=("robots.txt (checked 2026-08-15): /collections/ and /products/ allowed for generic UA, "
                          "only sort/filter query-string variants disallowed; sitemap.xml published. "
                          "ToS (checked 2026-08-15): no scraping restriction found. Manufacturer's own storefront. "
                          "discover() only runs against a collection URL a human supplies, never scheduled.")),
            Source(key="official_bang_dream", name="BanG Dream! Official Site", kind=SourceKind.official,
                   base_url="https://bang-dream.com", trust_priority=100,
                   crawl_policy=CrawlPolicy.manual_import_only,
                   notes="Official goods page URL not yet confirmed; treat as manual import until verified."),
            Source(key="amiami", name="AmiAmi", kind=SourceKind.retailer, base_url="https://www.amiami.com",
                   trust_priority=60, crawl_policy=CrawlPolicy.manual_import_only,
                   notes="robots.txt fetch inconclusive during research; needs manual ToS confirmation before auto crawl."),
            Source(key="suruga_ya", name="Suruga-ya", kind=SourceKind.secondhand, base_url="https://www.suruga-ya.jp",
                   trust_priority=40, crawl_policy=CrawlPolicy.manual_import_only,
                   notes="robots.txt allows generic UAs with use=reference signal; still needs a ToS read-through before enabling auto."),
            Source(key="mercari_jp", name="Mercari Japan", kind=SourceKind.secondhand, base_url="https://jp.mercari.com",
                   trust_priority=20, crawl_policy=CrawlPolicy.manual_import_only,
                   notes="Marketplace ToS typically restricts scraping regardless of robots.txt; manual import only."),
            Source(key="search_discovery", name="Search Engine Discovery", kind=SourceKind.search,
                   trust_priority=10, crawl_policy=CrawlPolicy.search_discovery_only,
                   notes="Not wired to a live search provider yet; see pipeline/sources/search_discovery.py."),
        ]
        db.add_all(sources)
        db.flush()
        manual_source = sources[0]

        def make_item(*, name, jp_name, character_ids, item_type, price, product_number, completeness_extra=None):
            fields = dict(
                canonical_name=name,
                japanese_name=jp_name,
                character_ids=character_ids,
                band_id=band.id,
                series="BanG Dream! Girls Band Party!",
                item_type_id=item_type.id,
                manufacturer="Bushiroad",
                release_date=dt.date(2025, 4, 1),
                release_date_source="seed data",
                release_date_confidence=1.0,
                official_price=price,
                currency="JPY",
                product_number=product_number,
                created_by="manual",
                updated_by="manual",
            )
            fields.update(completeness_extra or {})
            item = CatalogItem(**fields)
            db.add(item)
            db.flush()
            db.add(
                CatalogItemImage(
                    catalog_item_id=item.id,
                    image_url=placeholder_data_uri(name),
                    is_primary=True,
                )
            )
            return item

        kasumi_items = [
            make_item(name="Kasumi Toyama Can Badge", jp_name="戸山香澄 缶バッジ", character_ids=[kasumi.id],
                      item_type=badge, price=770, product_number="BD-K-001"),
            make_item(name="Kasumi Toyama Acrylic Stand", jp_name="戸山香澄 アクリルスタンド", character_ids=[kasumi.id],
                      item_type=acrylic_stand, price=1650, product_number="BD-K-002"),
            make_item(name="Kasumi Toyama Acrylic Keychain", jp_name="戸山香澄 アクリルキーホルダー",
                      character_ids=[kasumi.id], item_type=acrylic_keychain, price=1320, product_number="BD-K-003"),
            make_item(name="Kasumi Toyama Live Ver. Badge", jp_name="戸山香澄 缶バッジ Live Ver.",
                      character_ids=[kasumi.id], item_type=badge, price=770, product_number="BD-K-004"),
            make_item(name="Kasumi Toyama Birthday 2025 Acrylic Stand", jp_name="戸山香澄 誕生日2025 アクリルスタンド",
                      character_ids=[kasumi.id], item_type=acrylic_stand, price=1980, product_number="BD-K-005"),
        ]

        arisa_items = [
            make_item(name="Arisa Ichigaya Can Badge", jp_name="市ヶ谷有咲 缶バッジ", character_ids=[arisa.id],
                      item_type=badge, price=770, product_number="BD-A-001"),
            make_item(name="Arisa Ichigaya Acrylic Stand", jp_name="市ヶ谷有咲 アクリルスタンド", character_ids=[arisa.id],
                      item_type=acrylic_stand, price=1650, product_number="BD-A-002"),
            make_item(name="Arisa Ichigaya Acrylic Keychain", jp_name="市ヶ谷有咲 アクリルキーホルダー",
                      character_ids=[arisa.id], item_type=acrylic_keychain, price=1320, product_number="BD-A-003"),
            make_item(name="Arisa Ichigaya Live Ver. Badge", jp_name="市ヶ谷有咲 缶バッジ Live Ver.",
                      character_ids=[arisa.id], item_type=badge, price=770, product_number="BD-A-004"),
            make_item(name="Arisa Ichigaya Birthday 2025 Acrylic Stand", jp_name="市ヶ谷有咲 誕生日2025 アクリルスタンド",
                      character_ids=[arisa.id], item_type=acrylic_stand, price=1980, product_number="BD-A-005"),
        ]

        group_items = [
            make_item(name="Kasumi & Arisa Duo Can Badge", jp_name="香澄・有咲 缶バッジ",
                      character_ids=[kasumi.id, arisa.id], item_type=badge, price=880, product_number="BD-G-001"),
            make_item(name="Poppin'Party All Members Acrylic Stand Set",
                      jp_name="ポピパ 全員 アクリルスタンドセット",
                      character_ids=[kasumi.id, arisa.id, tae.id, rimi.id, saaya.id],
                      item_type=acrylic_stand, price=8250, product_number="BD-G-002",
                      completeness_extra={"manufacturer": None}),  # deliberately incomplete, to exercise "missing fields"
        ]

        all_items = kasumi_items + arisa_items + group_items
        db.flush()

        # Personal collection: mark a handful owned/wishlisted so MyCollection has data to show.
        owned = [kasumi_items[0], kasumi_items[1], arisa_items[0], group_items[0]]
        wishlisted = [kasumi_items[3], arisa_items[3], group_items[1]]
        for item in owned:
            db.add(
                UserCollection(
                    catalog_item_id=item.id,
                    status=CollectionStatus.owned,
                    quantity=1,
                    purchase_price=item.official_price,
                    currency="JPY",
                    purchase_date=dt.date(2025, 5, 1),
                    purchase_source="Seed data",
                )
            )
        for item in wishlisted:
            db.add(UserCollection(catalog_item_id=item.id, status=CollectionStatus.wishlist, quantity=0))
        for item in all_items:
            if item not in owned and item not in wishlisted:
                db.add(UserCollection(catalog_item_id=item.id, status=CollectionStatus.not_owned, quantity=0))

        # A few pending review-queue candidates so /review can be exercised without running the crawler.
        raw1 = RawProduct(
            source_id=manual_source.id,
            source_url="https://example.com/mock-listing-1",
            raw_title="戸山香澄 缶バッジ (再販)",
            raw_price=770,
            raw_currency="JPY",
            raw_images=[{"url": placeholder_data_uri("Reprint Badge")}],
            raw_metadata={"note": "seed mock raw product, not real"},
            parser_version="seed-v1",
        )
        raw2 = RawProduct(
            source_id=manual_source.id,
            source_url="https://example.com/mock-listing-2",
            raw_title="Poppin'Party Kasumi New Keychain 2026",
            raw_price=1200,
            raw_currency="JPY",
            raw_images=[{"url": placeholder_data_uri("New Keychain")}],
            raw_metadata={"note": "seed mock raw product, not real"},
            parser_version="seed-v1",
        )
        db.add_all([raw1, raw2])
        db.flush()

        db.add_all(
            [
                Candidate(
                    raw_product_id=raw1.id,
                    canonical_name="Kasumi Toyama Can Badge (Reprint)",
                    japanese_name="戸山香澄 缶バッジ (再販)",
                    character_ids=[kasumi.id],
                    item_type_id=badge.id,
                    product_number="BD-K-001",
                    price=770,
                    currency="JPY",
                    images=[{"url": placeholder_data_uri("Reprint Badge")}],
                    confidence=0.55,
                    status=CandidateStatus.pending,
                ),
                Candidate(
                    raw_product_id=raw2.id,
                    canonical_name="Kasumi Toyama New Keychain 2026",
                    japanese_name=None,
                    character_ids=[kasumi.id],
                    item_type_id=item_types[3].id,
                    price=1200,
                    currency="JPY",
                    images=[{"url": placeholder_data_uri("New Keychain")}],
                    confidence=0.68,
                    status=CandidateStatus.pending,
                ),
            ]
        )

        db.commit()
        print(f"Seeded {len(all_items)} catalog items, {len(characters)} characters, {len(sources)} sources, 2 review candidates.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
