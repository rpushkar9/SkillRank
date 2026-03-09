import type { SearchResult } from "@/types/search";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

export interface ExplainResponse {
  lines: string[];
  took_ms: number;
}

export async function explainSkills(
  query: string,
  skills: SearchResult[]
): Promise<ExplainResponse> {
  const url = API_BASE_URL ? `${API_BASE_URL}/api/v1/explain` : "/api/v1/explain";

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      query,
      skills: skills.map((s) => ({ name: s.name, description: s.description })),
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Explain request failed.");
  }

  return response.json() as Promise<ExplainResponse>;
}
