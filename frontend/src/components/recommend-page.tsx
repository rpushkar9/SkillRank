"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { recommendSkills } from "@/lib/recommend-client";
import type { SearchResult } from "@/types/search";

import styles from "./recommend-page.module.css";

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
  if (!text) return "";
  if (text.length <= length) return text;
  return `${text.slice(0, length).trim()}...`;
}

export function RecommendPage() {
  const [folderPath, setFolderPath] = useState("");
  const [status, setStatus] = useState("Enter your project folder path above.");
  const [error, setError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasRecommended, setHasRecommended] = useState(false);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [results, setResults] = useState<SearchResult[]>([]);

  async function runRecommend(event?: FormEvent) {
    event?.preventDefault();

    const clean = folderPath.trim();
    if (!clean) {
      setError(false);
      setStatus("Enter a folder path first.");
      setResults([]);
      setPrompts([]);
      setHasRecommended(false);
      return;
    }

    setIsLoading(true);
    setError(false);
    setStatus("Reading conversation history...");

    try {
      const payload = await recommendSkills(clean);
      setPrompts(payload.prompts_used);
      setResults(payload.results);
      setHasRecommended(true);
      setStatus(
        `Found ${payload.results.length} skill(s) in ${payload.took_ms.toFixed(1)} ms.`
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Recommendation failed.";
      setError(true);
      setStatus(message);
      setResults([]);
      setPrompts([]);
      setHasRecommended(true);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className={styles.screen}>
      <div className={styles.page}>
        <header className={styles.header}>
          <h1 className={styles.title}>SkillRank</h1>
          <p className={styles.tagline}>
            Get skill recommendations based on your recent AI conversations.
          </p>
          <div className={styles.nav}>
            <Link className={styles.navLink} href="/">
              Search skills manually
            </Link>
          </div>
        </header>

        <form className={styles.searchRow} onSubmit={runRecommend}>
          <label htmlFor="folder-path" className={styles.srOnly}>
            Project folder path
          </label>
          <input
            id="folder-path"
            className={styles.searchInput}
            type="text"
            placeholder="e.g. /Users/you/projects/my-project"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            autoComplete="off"
          />
          <button className={styles.searchButton} type="submit" disabled={isLoading}>
            {isLoading ? "Loading..." : "Get Recommendations"}
          </button>
        </form>

        <div
          className={`${styles.status} ${error ? styles.statusError : ""}`}
          aria-live="polite"
        >
          {status}
        </div>

        {hasRecommended && !error && prompts.length > 0 && (
          <div className={styles.section}>
            <p className={styles.sectionTitle}>Recent Prompts Used</p>
            <ol className={styles.promptList}>
              {prompts.map((prompt, i) => (
                <li key={i} className={styles.promptItem}>
                  {truncate(prompt, 200)}
                </li>
              ))}
            </ol>
          </div>
        )}

        <div className={styles.results}>
          {hasRecommended && results.length === 0 && !isLoading && !error ? (
            <div className={styles.empty}>
              No skills found for your recent prompts. Try a different project folder.
            </div>
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
      </div>
    </div>
  );
}
