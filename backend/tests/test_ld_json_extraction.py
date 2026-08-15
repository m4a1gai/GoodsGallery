from pipeline.sources.common import extract_product, find_product_ld_json

# Captured verbatim (structure) from a real bushiroad-store.com (Shopify) product
# page: offers is a *list*, image is an ImageObject, not a bare string — the
# original parser assumed dict/str for both and silently dropped the price.
SHOPIFY_PRODUCT_LD_JSON = {
    "@context": "http://schema.org",
    "@type": "Product",
    "offers": [
        {
            "@type": "Offer",
            "name": "Default Title",
            "availability": "https://schema.org/InStock",
            "price": 1000.0,
            "priceCurrency": "JPY",
            "sku": "4570194433626",
        }
    ],
    "gtin13": "4570194433626",
    "name": "BanG Dream!　ジオラマアクリルスタンド 戸山 香澄 Sweet Track ver.",
    "image": {
        "@type": "ImageObject",
        "url": "https://bushiroad-store.com/cdn/shop/files/BDP_acril_ari1_1024x.jpg?v=1777265417",
    },
}


def test_extract_product_handles_offers_as_list():
    extracted = extract_product(SHOPIFY_PRODUCT_LD_JSON)
    assert extracted.price == 1000.0
    assert extracted.currency == "JPY"


def test_extract_product_handles_image_object():
    extracted = extract_product(SHOPIFY_PRODUCT_LD_JSON)
    assert extracted.images == ["https://bushiroad-store.com/cdn/shop/files/BDP_acril_ari1_1024x.jpg?v=1777265417"]


def test_extract_product_prefers_gtin_for_product_number():
    extracted = extract_product(SHOPIFY_PRODUCT_LD_JSON)
    assert extracted.product_number == "4570194433626"


def test_extract_product_handles_offers_as_plain_dict():
    entry = {
        "@type": "Product",
        "name": "Some Item",
        "offers": {"@type": "Offer", "price": "500", "priceCurrency": "JPY"},
        "image": "https://example.com/img.jpg",
    }
    extracted = extract_product(entry)
    assert extracted.price == 500.0
    assert extracted.images == ["https://example.com/img.jpg"]


def test_find_product_ld_json_skips_non_product_blocks():
    breadcrumb_block = {"@type": "BreadcrumbList", "itemListElement": []}
    result = find_product_ld_json([breadcrumb_block, SHOPIFY_PRODUCT_LD_JSON])
    assert result is not None
    assert result.price == 1000.0


def test_find_product_ld_json_returns_none_when_absent():
    assert find_product_ld_json([{"@type": "BreadcrumbList"}]) is None
