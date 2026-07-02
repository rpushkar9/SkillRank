"""Ollama LLM client for query expansion and result explanation."""

from __future__ import annotations

import httpx


_EXPAND_PROMPT = """\
The user wants to: "{query}"

Think about what technical skills and tools they need to accomplish this.
Available skill categories include: frontend frameworks (React, Vue, Angular, Next.js, Svelte, Astro), \
UI/design (Tailwind, shadcn-ui, accessibility, Figma), backend (Node.js, Python, FastAPI, Express, GraphQL, REST APIs), \
databases (PostgreSQL, MongoDB, Prisma, Redis, Supabase), DevOps/cloud (Docker, AWS, Cloudflare, CI/CD, Terraform), \
testing (Vitest, Playwright, Jest, pytest), AI/agents (LLM integration, MCP tools, RAG, embeddings, Claude/OpenAI SDKs), \
mobile (Swift, iOS, Android, Flutter), security (auth, OAuth, JWT), and developer productivity (documentation, markdown, code quality).
Generate a concise search query (2-4 sentences) listing the most relevant skill areas from the categories above.
Return ONLY the expanded query text, no preamble or explanation.\
"""

_EXPLAIN_PROMPT = """\
The user wants to: "{query}"

Recommended skills:
{skills}

For each skill write ONE line in this exact format:
[skill-name] — [one sentence why it specifically helps the user accomplish their goal]

If two skills are very similar in purpose, group them on one line:
[skill-a] / [skill-b] — [one sentence, note which is more relevant]

Output ONLY the lines, one per skill or group. No intro, no summary, no extra text.\
"""


class OllamaService:
    """Calls a local Ollama instance for query expansion and result explanation."""

    def __init__(self, base_url: str, model: str, timeout: float):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _generate(self, prompt: str) -> str:
        """Call /api/generate and return the response text. Raises on failure."""
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["response"].strip()

    def expand_query(self, query: str) -> str:
        """Return a skill-focused expanded version of the user query.

        Falls back to the original query on any error (Ollama not running, timeout, etc.).
        """
        try:
            prompt = _EXPAND_PROMPT.format(query=query)
            expanded = self._generate(prompt)
            return expanded if expanded else query
        except Exception:
            return query

    def explain_results(self, query: str, skills: list[tuple[str, str]]) -> list[str]:
        """Return per-skill explanation lines for why the skills fit the user's goal.

        Each line is either:
          "skill-name — one sentence why it helps"
          "skill-a / skill-b — grouped if similar"

        Returns an empty list on any error.
        """
        try:
            skills_text = "\n".join(
                f"{i + 1}. {name} — {desc[:100]}"
                for i, (name, desc) in enumerate(skills)
            )
            prompt = _EXPLAIN_PROMPT.format(query=query, skills=skills_text)
            raw = self._generate(prompt)
            lines = [line.strip() for line in raw.splitlines() if line.strip()]
            return lines
        except Exception:
            return []
