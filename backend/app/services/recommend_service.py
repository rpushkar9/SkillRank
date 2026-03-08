"""Recommendation service: reads Claude conversation history and recommends skills."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from app.core.config import Settings
from app.core.errors import ProjectNotFoundError, RecommendExecutionError
from app.db.qdrant import QdrantStore
from app.schemas.search import SearchResult
from app.services.embedder import EmbedderService


def _folder_to_slug(folder_path: str) -> str:
    """Convert an absolute folder path to a Claude project slug.

    Example: /Users/foo/F1/-> -Users-foo-F1-Name-With-Bar
    """
    normalized = folder_path.rstrip("/")
    return normalized.replace("/", "-").replace(" ", "-")


def _extract_prompts_from_file(jsonl_path: Path, needed: int) -> list[str]:
    """Read a JSONL file and return up to `needed` recent user prompts."""
    prompts: list[str] = []
    try:
        lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return prompts

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        if obj.get("type") != "user":
            continue

        message = obj.get("message", {})
        content = message.get("content", [])
        if not isinstance(content, list):
            continue

        # Skip tool result messages (Bash/tool output returned to Claude)
        if any(
            isinstance(item, dict) and item.get("type") == "tool_result"
            for item in content
        ):
            continue

        # Only keep text items that are NOT system/IDE injections (those start with "<")
        texts = [
            item["text"]
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and not item["text"].lstrip().startswith("<")
        ]
        combined = " ".join(texts).strip()

        # Skip empty or very short entries
        if not combined or len(combined) < 10:
            continue

        prompts.append(combined)
        if len(prompts) >= needed:
            break

    return prompts


class RecommendService:
    """Recommends skills based on recent Claude conversation prompts."""

    def __init__(
        self,
        settings: Settings,
        qdrant_store: QdrantStore,
        embedder: EmbedderService,
    ):
        self.settings = settings
        self.qdrant_store = qdrant_store
        self.embedder = embedder

    def _find_projects_base(self) -> Path:
        if self.settings.claude_projects_base:
            return Path(self.settings.claude_projects_base)
        return Path.home() / ".claude" / "projects"

    def recommend(self, folder_path: str) -> tuple[list[str], list[SearchResult]]:
        """Return (prompts_used, ranked_results) for the given project folder."""
        if not folder_path or not folder_path.strip():
            raise RecommendExecutionError("folder_path must not be empty.")

        slug = _folder_to_slug(folder_path.strip())
        project_dir = self._find_projects_base() / slug

        if not project_dir.exists() or not project_dir.is_dir():
            raise ProjectNotFoundError(
                f"No Claude project found for path '{folder_path}'. "
                f"Expected directory: {project_dir}"
            )

        jsonl_files = sorted(
            project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not jsonl_files:
            raise RecommendExecutionError(
                f"No conversation history (.jsonl) found in {project_dir}."
            )

        k = self.settings.k_recent_prompts
        prompts: list[str] = []
        for jf in jsonl_files:
            if len(prompts) >= k:
                break
            prompts.extend(_extract_prompts_from_file(jf, k - len(prompts)))

        if not prompts:
            raise RecommendExecutionError(
                "No usable user prompts found in conversation history."
            )

        # Embed each prompt, query Qdrant, accumulate scores
        skill_scores: dict[str, list[float]] = defaultdict(list)
        skill_payloads: dict[str, dict] = {}

        try:
            for prompt in prompts:
                vector = self.embedder.embed_query(prompt)
                hits = self.qdrant_store.search(
                    query_vector=vector, limit=self.settings.qdrant_top_n
                )
                for hit in hits:
                    payload = hit.payload or {}
                    skill_id = str(payload.get("skill_id", ""))
                    if not skill_id:
                        continue
                    skill_scores[skill_id].append(float(hit.score or 0.0))
                    skill_payloads[skill_id] = payload
        except Exception as exc:
            raise RecommendExecutionError(
                f"Failed to query vector database: {exc}"
            ) from exc

        # Average scores and rank
        ranked = sorted(
            skill_scores.keys(),
            key=lambda sid: sum(skill_scores[sid]) / len(skill_scores[sid]),
            reverse=True,
        )

        results: list[SearchResult] = []
        for skill_id in ranked[: self.settings.top_n_recommend]:
            payload = skill_payloads[skill_id]
            avg_score = sum(skill_scores[skill_id]) / len(skill_scores[skill_id])
            results.append(
                SearchResult(
                    skill_id=skill_id,
                    name=str(payload.get("name", "")),
                    description=str(payload.get("description", "")),
                    skill_url=str(payload.get("skill_url", "")),
                    weekly_installs=int(payload.get("weekly_installs", 0) or 0),
                    total_installs=int(payload.get("total_installs", 0) or 0),
                    first_seen=payload.get("first_seen"),
                    score=round(avg_score, 6),
                )
            )

        return prompts, results
