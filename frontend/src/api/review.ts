import { api } from "./client";
import type { Candidate, CandidateStatus } from "../types";

export function fetchCandidates(status: CandidateStatus = "pending"): Promise<Candidate[]> {
  return api.get(`/api/review/candidates?status=${status}`);
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
