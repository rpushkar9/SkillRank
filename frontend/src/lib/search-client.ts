import type { SearchResponse } from "@/types/search";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

function buildSearchUrl(query: string, k: number): string {
  const base = API_BASE_URL || "";
  const path = `${base}/api/v1/search`;

  const url = new URL(path, typeof window !== "undefined" ? window.location.origin : "http://localhost");
  url.searchParams.set("q", query);
  url.searchParams.set("k", String(k));

  // If API_BASE_URL is absolute, return absolute URL. Otherwise, return path+query.
  if (API_BASE_URL) {
    return url.toString();
  }

  return `${url.pathname}${url.search}`;
}

export async function searchSkills(query: string, k = 5): Promise<SearchResponse> {
  const response = await fetch(buildSearchUrl(query, k), {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  const payload = (await response.json()) as SearchResponse | { detail?: string; error?: string };

  if (!response.ok) {
    const message =
      (payload as { detail?: string; error?: string }).detail ||
      (payload as { detail?: string; error?: string }).error ||
      "Search request failed.";
    throw new Error(message);
  }

  return payload as SearchResponse;
}
