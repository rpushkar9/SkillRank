import type { SearchResult } from "./search";

export interface RecommendRequest {
  folder_path: string;
}

export interface RecommendResponse {
  folder_path: string;
  prompts_used: string[];
  results: SearchResult[];
  took_ms: number;
}
