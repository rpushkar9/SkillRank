export interface SearchResult {
  skill_id: string;
  name: string;
  description: string;
  skill_url: string;
  weekly_installs: number;
  total_installs: number;
  first_seen?: string | null;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
  took_ms: number;
  expanded_query?: string | null;
  expand_ms?: number | null;
}
