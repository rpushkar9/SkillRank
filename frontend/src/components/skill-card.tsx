import type { SearchResult } from "@/types/search";
import { formatNumber, matchLabel, truncate } from "@/lib/utils";
import styles from "./skill-card.module.css";

interface SkillCardProps {
  result: SearchResult;
  rank: number;
  truncateLength?: number;
}

export function SkillCard({ result, rank, truncateLength = 260 }: SkillCardProps) {
  const { label, tier } = matchLabel(result.score);

  return (
    <article
      className={styles.card}
      data-tier={tier}
      style={{ "--card-index": rank - 1 } as React.CSSProperties}
    >
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
        <span className={styles.matchBadge} data-tier={tier}>
          {label}
        </span>
      </div>

      <p className={styles.cardDesc}>{truncate(result.description, truncateLength)}</p>

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
  );
}

interface SkillCardSkeletonProps {
  index: number;
}

export function SkillCardSkeleton({ index }: SkillCardSkeletonProps) {
  return (
    <div
      className={styles.skeleton}
      style={{ "--card-index": index } as React.CSSProperties}
      aria-hidden="true"
    />
  );
}
