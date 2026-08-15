export interface Character {
  id: number;
  name: string;
  japanese_name: string | null;
  english_name: string | null;
  sort_order: number;
}

export interface ItemType {
  id: number;
  code: string;
  label_en: string;
  label_ja: string | null;
}

export interface CatalogItemListItem {
  id: number;
  canonical_name: string;
  japanese_name: string | null;
  character_ids: number[];
  item_type_id: number | null;
  official_price: number | null;
  currency: string | null;
  data_completeness: number;
  primary_image_url: string | null;
}

export interface CatalogItemImage {
  id: number;
  image_url: string;
  source_item_url: string | null;
  is_primary: boolean;
}

export interface CatalogItemSource {
  id: number;
  source_id: number;
  source_url: string;
  source_price: number | null;
  last_seen_at: string | null;
}

export interface CatalogItemDetail {
  id: number;
  canonical_name: string;
  japanese_name: string | null;
  original_title: string | null;
  translated_title: string | null;
  translation_source: string | null;
  character_ids: number[];
  band_id: number | null;
  series: string | null;
  item_type_id: number | null;
  manufacturer: string | null;
  release_date: string | null;
  release_date_source: string | null;
  release_date_confidence: number | null;
  official_price: number | null;
  currency: string | null;
  product_number: string | null;
  data_completeness: number;
  missing_fields: string[];
  images: CatalogItemImage[];
  item_sources: CatalogItemSource[];
}

export type CollectionStatus = "owned" | "wishlist" | "not_owned";

export interface UserCollection {
  id: number;
  catalog_item_id: number;
  status: CollectionStatus;
  quantity: number;
  purchase_price: number | null;
  currency: string | null;
  purchase_date: string | null;
  purchase_source: string | null;
  notes: string | null;
}

export interface CollectionStats {
  catalog_total: number;
  owned_total: number;
  wishlist_total: number;
  completion_pct: number;
  total_spent: number;
  by_character: Record<string, { owned: number; total: number }>;
}

export type CandidateStatus = "pending" | "accepted" | "rejected" | "merged";

export interface Candidate {
  id: number;
  raw_product_id: number;
  canonical_name: string;
  japanese_name: string | null;
  character_ids: number[];
  series: string | null;
  item_type_id: number | null;
  manufacturer: string | null;
  price: number | null;
  currency: string | null;
  product_number: string | null;
  images: { url: string }[];
  confidence: number;
  status: CandidateStatus;
  created_at: string;
  source_url: string | null;
}

export type SourceKind = "official" | "manufacturer" | "retailer" | "secondhand" | "search" | "user_submitted";
export type CrawlPolicy = "auto" | "search_discovery_only" | "manual_import_only" | "disabled";

export interface Source {
  id: number;
  key: string;
  name: string;
  kind: SourceKind;
  base_url: string | null;
  trust_priority: number;
  crawl_policy: CrawlPolicy;
  robots_checked_at: string | null;
  notes: string | null;
}
