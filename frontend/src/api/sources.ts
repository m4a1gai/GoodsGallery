import { api } from "./client";
import type { Source } from "../types";

export function fetchSources(): Promise<Source[]> {
  return api.get(`/api/sources`);
}

export interface CrawlResult {
  discovered: number;
  created: number;
  skipped_already_seen: number;
  errors: number;
  candidate_ids: number[];
}

export function triggerCrawl(
  sourceKey: string,
  payload: { start_url: string; max_pages?: number; limit?: number }
): Promise<CrawlResult> {
  return api.post(`/api/sources/${sourceKey}/crawl`, payload);
}
