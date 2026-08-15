import { api } from "./client";
import type { CollectionStats, CollectionStatus, UserCollection } from "../types";

export function fetchCollection(status?: CollectionStatus): Promise<UserCollection[]> {
  const qs = status ? `?status=${status}` : "";
  return api.get(`/api/collection/items${qs}`);
}

export function fetchCollectionStats(): Promise<CollectionStats> {
  return api.get(`/api/collection/stats`);
}

export function updateCollection(
  catalogItemId: number,
  payload: Partial<Omit<UserCollection, "id" | "catalog_item_id">>
): Promise<UserCollection> {
  return api.put(`/api/collection/items/${catalogItemId}`, payload);
}
