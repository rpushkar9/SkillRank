import type { RecommendResponse } from "@/types/recommend";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

function buildRecommendUrl(): string {
  const path = `${API_BASE_URL}/api/v1/recommend`;
  return API_BASE_URL ? path : "/api/v1/recommend";
}

export async function recommendSkills(folderPath: string): Promise<RecommendResponse> {
  const response = await fetch(buildRecommendUrl(), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ folder_path: folderPath }),
    cache: "no-store",
  });

  const payload = (await response.json()) as RecommendResponse | { detail?: string; error?: string };

  if (!response.ok) {
    const message =
      (payload as { detail?: string; error?: string }).detail ||
      (payload as { detail?: string; error?: string }).error ||
      "Recommendation failed.";
    throw new Error(message);
  }

  return payload as RecommendResponse;
}
