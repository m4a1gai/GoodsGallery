import { api } from "./client";
import type { CatalogItemDetail, CatalogItemImage, CatalogItemListItem, Character, ItemType } from "../types";

export interface CatalogFilters {
  characterId?: number;
  characterMode?: "includes" | "exact";
  itemTypeId?: number;
  search?: string;
}

export function fetchCatalogItems(filters: CatalogFilters = {}): Promise<CatalogItemListItem[]> {
  const params = new URLSearchParams();
  if (filters.characterId !== undefined) params.set("character_id", String(filters.characterId));
  if (filters.characterMode) params.set("character_mode", filters.characterMode);
  if (filters.itemTypeId !== undefined) params.set("item_type_id", String(filters.itemTypeId));
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return api.get(`/api/catalog/items${qs ? `?${qs}` : ""}`);
}

export function fetchCatalogItem(id: number): Promise<CatalogItemDetail> {
  return api.get(`/api/catalog/items/${id}`);
}

export function fetchCharacters(): Promise<Character[]> {
  return api.get(`/api/catalog/characters`);
}

export function fetchItemTypes(): Promise<ItemType[]> {
  return api.get(`/api/catalog/item-types`);
}

export function addCatalogItemImage(
  itemId: number,
  payload: { image_url: string; source_item_url?: string; is_primary?: boolean }
): Promise<CatalogItemImage> {
  return api.post(`/api/catalog/items/${itemId}/images`, payload);
}

export function setPrimaryCatalogItemImage(itemId: number, imageId: number): Promise<CatalogItemImage> {
  return api.patch(`/api/catalog/items/${itemId}/images/${imageId}/primary`, {});
}

export async function deleteCatalogItemImage(itemId: number, imageId: number): Promise<void> {
  await api.delete(`/api/catalog/items/${itemId}/images/${imageId}`);
}
