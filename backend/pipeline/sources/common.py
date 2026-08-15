"""Shared JSON-LD Product extraction, reused by any adapter that parses
schema.org/Product structured data (which is most storefronts, and in
particular every Shopify-based store — Bushiroad Store included).

Split out from manual_import.py after a real fetch against
bushiroad-store.com showed the naive version (offers as a dict, image as a
plain string) silently dropped the price: Shopify emits `offers` as a *list*
of Offer objects and `image` as an ImageObject, not a bare string. Both
shapes are handled here now, along with sku/gtin as a product_number
candidate — schema.org doesn't have a "product number" field, but a GTIN/SKU
is the closest stable identifier a storefront publishes, and it's exactly
the kind of strong signal the dedup matcher prioritizes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExtractedProduct:
    title: str | None = None
    price: float | None = None
    currency: str | None = None
    images: list[str] | None = None
    product_number: str | None = None
    raw: dict | None = None

    def __post_init__(self):
        if self.images is None:
            self.images = []


def _first_offer(offers) -> dict | None:
    if isinstance(offers, list):
        for o in offers:
            if isinstance(o, dict):
                return o
        return None
    if isinstance(offers, dict):
        return offers
    return None


def _extract_images(image) -> list[str]:
    if isinstance(image, str):
        return [image]
    if isinstance(image, dict):
        url = image.get("url") or image.get("contentUrl")
        return [url] if url else []
    if isinstance(image, list):
        out: list[str] = []
        for entry in image:
            out.extend(_extract_images(entry))
        return out
    return []


def extract_product(entry: dict) -> ExtractedProduct:
    """`entry` is one JSON-LD node already known to be @type Product."""
    offer = _first_offer(entry.get("offers"))
    price = offer.get("price") if offer else None
    currency = offer.get("priceCurrency") if offer else None

    product_number = entry.get("sku") or entry.get("gtin13") or entry.get("gtin") or entry.get("productId")
    if not product_number and offer:
        product_number = offer.get("sku")

    return ExtractedProduct(
        title=entry.get("name"),
        price=float(price) if price not in (None, "") else None,
        currency=currency,
        images=_extract_images(entry.get("image")),
        product_number=str(product_number) if product_number else None,
        raw=entry,
    )


def find_product_ld_json(json_ld_blocks: list[dict]) -> ExtractedProduct | None:
    for data in json_ld_blocks:
        candidates = data if isinstance(data, list) else [data]
        for entry in candidates:
            if isinstance(entry, dict) and entry.get("@type") in ("Product", "product"):
                return extract_product(entry)
    return None
