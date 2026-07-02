import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return String(value);
}

export function truncate(text: string, length: number): string {
  if (!text) return "";
  if (text.length <= length) return text;
  return `${text.slice(0, length).trim()}...`;
}

export function matchLabel(score: number): {
  label: string;
  tier: "strong" | "good" | "relevant";
} {
  if (score >= 0.65) return { label: "Great match", tier: "strong" };
  if (score >= 0.45) return { label: "Good match", tier: "good" };
  return { label: "Relevant", tier: "relevant" };
}
