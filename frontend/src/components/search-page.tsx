"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { explainSkills } from "@/lib/explain-client";
import { searchSkills } from "@/lib/search-client";
import { formatNumber } from "@/lib/utils";
import type { SearchResult } from "@/types/search";
import { SkillCard, SkillCardSkeleton } from "@/components/skill-card";

import styles from "./search-page.module.css";

const DEFAULT_LIMIT = 5;

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
          <div className={styles.searchInputWrap}>
            <input
              id="skill-query"
              className={styles.searchInput}
              type="text"
              placeholder="e.g. I want to build a portfolio website"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              autoComplete="off"
            />
          </div>
          <button
            className={styles.searchButton}
            type="submit"
            disabled={isLoading}
            aria-busy={isLoading}
          >
            Search
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
            Query expansion: {formatNumber(expandMs)} ms
          </div>
        ) : null}

        {/* Skill cards */}
        <div className={styles.results}>
          {isLoading ? (
            [0, 1, 2].map((i) => <SkillCardSkeleton key={i} index={i} />)
          ) : null}

          {hasSearched && results.length === 0 && !isLoading ? (
            <div className={styles.empty}>No skills found. Try rephrasing your task.</div>
          ) : null}

          {!isLoading
            ? results.map((result, i) => (
                <SkillCard key={result.skill_id || result.name} result={result} rank={i + 1} />
              ))
            : null}
        </div>

        {/* Status line — below cards */}
        <div
          className={`${styles.status} ${error ? styles.statusError : ""}`}
          aria-live="polite"
        >
          {status}
        </div>

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
