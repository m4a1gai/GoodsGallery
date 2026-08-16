import { api } from "./client";
import type { Candidate, CandidateStatus } from "../types";

export function fetchCandidates(status: CandidateStatus = "pending"): Promise<Candidate[]> {
  return api.get(`/api/review/candidates?status=${status}`);
}

export function fetchCandidate(id: number): Promise<Candidate> {
  return api.get(`/api/review/candidates/${id}`);
}

export function acceptCandidate(id: number): Promise<Candidate> {
  return api.post(`/api/review/candidates/${id}/accept`);
}

export function rejectCandidate(id: number, reason?: string): Promise<Candidate> {
  return api.post(`/api/review/candidates/${id}/reject`, { reason });
}

export function editCandidateImages(id: number, images: { url: string }[]): Promise<Candidate> {
  return api.patch(`/api/review/candidates/${id}`, { images });
}

export interface SplitItem {
  canonical_name: string;
  japanese_name?: string;
  image_url: string;
}

export function splitCandidate(id: number, splits: SplitItem[]): Promise<{ catalog_item_ids: number[] }> {
  return api.post(`/api/review/candidates/${id}/split`, { splits });
}
