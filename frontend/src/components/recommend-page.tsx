"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { recommendSkills } from "@/lib/recommend-client";
import { truncate } from "@/lib/utils";
import type { SearchResult } from "@/types/search";
import { SkillCard, SkillCardSkeleton } from "@/components/skill-card";

import styles from "./recommend-page.module.css";

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
          <div className={styles.searchInputWrap}>
            <input
              id="folder-path"
              className={styles.searchInput}
              type="text"
              placeholder="e.g. /Users/you/projects/my-project"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              autoComplete="off"
            />
          </div>
          <button
            className={styles.searchButton}
            type="submit"
            disabled={isLoading}
            aria-busy={isLoading}
          >
            Get Recommendations
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
            <p className={styles.sectionTitle}>Analyzed from your session</p>
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
          {isLoading ? (
            [0, 1, 2].map((i) => <SkillCardSkeleton key={i} index={i} />)
          ) : null}

          {hasRecommended && results.length === 0 && !isLoading && !error ? (
            <div className={styles.empty}>
              No skills found for your recent prompts. Try a different project folder.
            </div>
          ) : null}

          {!isLoading
            ? results.map((result, i) => (
                <SkillCard key={result.skill_id || result.name} result={result} rank={i + 1} />
              ))
            : null}
        </div>
      </div>
    </div>
  );
}
