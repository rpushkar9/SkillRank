"use client";

import { FormEvent, useState } from "react";

import { searchSkills } from "@/lib/search-client";
import type { SearchResult } from "@/types/search";

import styles from "./search-page.module.css";

const DEFAULT_LIMIT = 5;

function formatNumber(value: number): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }

  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }

  return String(value);
}

function truncate(text: string, length: number): string {
  if (!text) {
    return "";
  }

  if (text.length <= length) {
    return text;
  }

  return `${text.slice(0, length).trim()}...`;
}

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Type a query and search.");
  const [error, setError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);

  async function runSearch(event?: FormEvent) {
    event?.preventDefault();

    const clean = query.trim();
    if (!clean) {
      setError(false);
      setStatus("Type a query first.");
      setResults([]);
      setHasSearched(false);
      return;
    }

    setIsLoading(true);
    setError(false);
    setStatus("Searching...");

    try {
      const payload = await searchSkills(clean, DEFAULT_LIMIT);
      setResults(payload.results);
      setHasSearched(true);
      setStatus(`Found ${payload.results.length} skill(s) in ${payload.took_ms.toFixed(1)} ms.`);
    } catch (searchError) {
      const message = searchError instanceof Error ? searchError.message : "Search failed.";
      setError(true);
      setStatus(message);
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className={styles.screen}>
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>SkillRank</h1>
          <p className={styles.tagline}>Search for AI skills using natural language.</p>
        </header>

        <form className={styles.searchRow} onSubmit={runSearch}>
          <label htmlFor="skill-query" className={styles.srOnly}>
            Search query
          </label>
          <input
            id="skill-query"
            className={styles.searchInput}
            type="text"
            placeholder="e.g. summarize long PDFs, extract tables from papers"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            autoComplete="off"
          />
          <button className={styles.searchButton} type="submit" disabled={isLoading}>
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        <div className={`${styles.status} ${error ? styles.statusError : ""}`} aria-live="polite">
          {status}
        </div>

        <div className={styles.results}>
          {hasSearched && results.length === 0 && !isLoading ? (
            <div className={styles.empty}>No skills found. Try rephrasing your task.</div>
          ) : null}

          {results.map((result) => (
            <article key={result.skill_id || result.name} className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>
                  {result.skill_url ? (
                    <a href={result.skill_url} target="_blank" rel="noopener noreferrer">
                      {result.name}
                    </a>
                  ) : (
                    result.name
                  )}
                </h2>
                <span className={styles.score}>score {result.score.toFixed(3)}</span>
              </div>

              <p className={styles.cardDesc}>{truncate(result.description, 260)}</p>

              <div className={styles.cardMeta}>
                <span>weekly: {formatNumber(result.weekly_installs)}</span>
                <span>total: {formatNumber(result.total_installs)}</span>
                {result.first_seen ? <span>first seen: {result.first_seen}</span> : null}
              </div>

              {result.skill_url ? (
                <a className={styles.cardLink} href={result.skill_url} target="_blank" rel="noopener noreferrer">
                  View skill
                </a>
              ) : null}
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
