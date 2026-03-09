"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { explainSkills } from "@/lib/explain-client";
import { searchSkills } from "@/lib/search-client";
import type { SearchResult } from "@/types/search";

import styles from "./search-page.module.css";

const DEFAULT_LIMIT = 5;

function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return String(value);
}

function truncate(text: string, length: number): string {
  if (!text) return "";
  if (text.length <= length) return text;
  return `${text.slice(0, length).trim()}...`;
}

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Type a query and search.");
  const [error, setError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [expandedQuery, setExpandedQuery] = useState<string | null>(null);
  const [expandMs, setExpandMs] = useState<number | null>(null);
  const [isExplaining, setIsExplaining] = useState(false);
  const [explanationLines, setExplanationLines] = useState<string[]>([]);

  async function runSearch(event?: FormEvent) {
    event?.preventDefault();

    const clean = query.trim();
    if (!clean) {
      setError(false);
      setStatus("Type a query first.");
      setResults([]);
      setExpandedQuery(null);
      setExpandMs(null);
      setExplanationLines([]);
      setHasSearched(false);
      return;
    }

    // Reset state
    setIsLoading(true);
    setError(false);
    setStatus("Interpreting query...");
    setResults([]);
    setHasSearched(false);
    setExpandedQuery(null);
    setExpandMs(null);
    setExplanationLines([]);
    setIsExplaining(false);

    try {
      // Phase 1: search (expand + embed + Qdrant)
      const payload = await searchSkills(clean, DEFAULT_LIMIT);
      setResults(payload.results);
      setExpandedQuery(payload.expanded_query ?? null);
      setExpandMs(payload.expand_ms ?? null);
      setHasSearched(true);
      setStatus(
        `Found ${payload.results.length} skill(s) | Search: ${payload.took_ms.toFixed(0)} ms`
      );
      setIsLoading(false);

      // Phase 2: explain (async, runs after cards are visible)
      if (payload.results.length > 0) {
        setIsExplaining(true);
        try {
          const exp = await explainSkills(clean, payload.results);
          setExplanationLines(exp.lines);
        } catch {
          // explanation failure is silent
        } finally {
          setIsExplaining(false);
        }
      }
    } catch (searchError) {
      const message = searchError instanceof Error ? searchError.message : "Search failed.";
      setError(true);
      setStatus(message);
      setResults([]);
      setHasSearched(true);
      setIsLoading(false);
    }
  }

  return (
    <div className={styles.screen}>
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>SkillRank</h1>
          <p className={styles.tagline}>Search for AI skills using natural language.</p>
          <div className={styles.nav}>
            <Link className={styles.navLink} href="/recommend">
              Try Skills Recommender
            </Link>
          </div>
        </header>

        <form className={styles.searchRow} onSubmit={runSearch}>
          <label htmlFor="skill-query" className={styles.srOnly}>
            Search query
          </label>
          <input
            id="skill-query"
            className={styles.searchInput}
            type="text"
            placeholder="e.g. I want to build a portfolio website"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            autoComplete="off"
          />
          <button className={styles.searchButton} type="submit" disabled={isLoading}>
            {isLoading ? "Searching..." : "Search"}
          </button>
        </form>

        {/* Interpreted as */}
        {expandedQuery ? (
          <div className={styles.expandedQuery}>
            <span className={styles.expandedLabel}>Interpreted as:</span>
            {expandedQuery}
          </div>
        ) : null}

        {/* Query expansion timing */}
        {expandMs != null ? (
          <div className={styles.expandTiming}>
            Query expansion: {expandMs.toFixed(0)} ms
          </div>
        ) : null}

        {/* Skill cards */}
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
                <a
                  className={styles.cardLink}
                  href={result.skill_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View skill
                </a>
              ) : null}
            </article>
          ))}
        </div>

        {/* Status line — below cards */}
        {hasSearched ? (
          <div
            className={`${styles.status} ${error ? styles.statusError : ""}`}
            aria-live="polite"
          >
            {status}
          </div>
        ) : (
          <div className={styles.status} aria-live="polite">
            {status}
          </div>
        )}

        {/* Why these skills — loads after cards */}
        {(isExplaining || explanationLines.length > 0) && results.length > 0 ? (
          <div className={styles.explanationCard}>
            <p className={styles.explanationLabel}>Why these skills?</p>
            {isExplaining && explanationLines.length === 0 ? (
              <p className={styles.explanationLoading}>Generating explanation...</p>
            ) : (
              <ul className={styles.explanationList}>
                {explanationLines.map((line, i) => (
                  <li key={i} className={styles.explanationLine}>
                    {line}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
