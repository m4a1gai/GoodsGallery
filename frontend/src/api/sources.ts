import { api } from "./client";
import type { Source } from "../types";

export function fetchSources(): Promise<Source[]> {
  return api.get(`/api/sources`);
}
