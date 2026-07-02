# SkillRank Evaluation

This document describes the evaluation methodology, ground truth, and quantitative results for the SkillRank search and recommendation system.

---

## 1. Methodology

### 1.1 Metrics

| Metric | Formula | Why included |
|--------|---------|-------------|
| **P@1** | hits in top-1 / 1 | Rewards getting the best result right |
| **P@3** | hits in top-3 / 3 | Primary metric; baseline = 0.20 from old pipeline |
| **P@5** | hits in top-5 / 5 | Broader coverage check |
| **MRR** | 1/rank of first hit | Rewards placing any relevant result high |
| **NDCG@3** | DCG / IDCG at k=3 | Handles graded relevance; partial credit |
| **Latency p50/p95** | ms per query, 4 warm runs | Free from API `took_ms`; SLA check |

MAP was omitted — too few relevant items per query for it to add signal over NDCG.

**Graded relevance scale:**
- **2** — Highly relevant: directly addresses the query intent.
- **1** — Partially relevant: related, might be useful, not the obvious choice.
- **0** — Not relevant (implicit default).

**Regression gate:** `eval_harness.py` exits with code 1 if mean P@3 < 0.15.

### 1.2 Dataset

- **Corpus size:** 921 skills scraped from the Claude skills directory.
- **Ground truth:** 20 queries in `test_cases/ground_truth.json` (10 original + 10 new).
- **Categories:** mobile-dev, research, data-analysis, document-processing, content-creation, devops, frontend, design, testing, code-quality, analytics, vague, unanswerable, non-dev.

### 1.3 Limitations

- Small ground truth (20 queries) — results have high variance.
- Exact skill-ID matching — synonymous skills score 0 even if semantically correct.
- No pooling — skills not in ground truth are assumed irrelevant regardless of quality.
- Latency measured on local development setup, not production.

---

## 2. Ground Truth

### 2.1 Critical finding: skill corpus mismatch

The original `ground_truth_top3.md` expected 30 skill IDs across 10 queries. After validation against the 921-skill corpus:

| Status | Count |
|--------|-------|
| **EXISTS** in corpus | 7 |
| **MISSING** from corpus | 23 |

Only 7/30 expected skills (23%) actually exist. This means the old P@3=0.20 was computed against a partially phantom ground truth — most zero-precision queries were zero because the expected skills do not exist, not because retrieval failed.

**Affected queries and replacements:**

| Query | Original GT skills (all missing) | Validated replacements |
|-------|----------------------------------|------------------------|
| Q1 ios/firebase | firebase-auth, ios-swift-development, developing-ios-apps | swiftui-expert-skill, mobile-ios-design, auth-implementation-patterns |
| Q3 research papers | research-paper-writer, scientific-writing, academic-research-writer | academic-writing-style, content-research-writer, latex-paper-en |
| Q4 csv/python | exploratory-data-analysis, csv-data-summarizer, pandas-data-analysis | *(none — marked unanswerable)* |
| Q5 pdf/markdown | pandoc, markdown-formatter, research-documentation | baoyu-format-markdown, baoyu-url-to-markdown |
| Q6 blog/seo | blog-post, seo-content-writer, seo-content-optimizer | seo-geo, content-strategy, pre-publish-post-assistant |
| Q7 github triage | github-issue-triage ✓, automate-github-issues, github-workflow-automation | github-issue-triage only |
| Q8 docker/cicd | docker-deployment, github-actions, cicd-pipeline-setup | devops-engineer, aws-skills |
| Q9 design system | design-system-patterns ✓, web-component-design ✓, design-system-starter | +design-systems |
| Q10 figma | implement-design ✓, wireframe-prototyping ✓, figma | +figma-implement-design |

**Unanswerable queries** (Q4, Q19): no relevant skills exist in corpus; system expected to return low-confidence results.

### 2.2 Query selection (10 new queries)

New queries (Q11–Q20) were selected to cover categories absent from the original 10:

| Query | Category | Rationale |
|-------|----------|-----------|
| Q11 unit tests typescript react | testing | Core developer workflow |
| Q12 code review security | code-quality | High-value dev task |
| Q13 kubernetes helm microservices | devops | Different devops angle from Q8 |
| Q14 gitops argocd flux | devops | IaC/GitOps workflow |
| Q15 email sequence saas marketing | content-creation | Non-dev content marketing |
| Q16 repurpose youtube transcript | content-creation | Multi-format repurposing |
| Q17 analytics events tracking | analytics | Product analytics use case |
| Q18 improve my code | vague | Intentionally underspecified |
| Q19 help me with my project | unanswerable | Maximally vague |
| Q20 business email client complaint | non-dev | Non-developer use case |

---

## 3. Quantitative Results

### 3.1 System comparison

Run `eval_harness.py` to populate this table. The old pipeline numbers are computed from `ground_truth_top3.md`.

| Metric | Old BM25+Vector (original 10 queries, phantom GT) | New Qdrant (validated GT) |
|--------|--------------------------------------------------|--------------------------|
| P@1 | — | *(run harness)* |
| **P@3** | **0.20** | *(run harness)* |
| **MRR** | **0.25** | *(run harness)* |
| NDCG@3 | — | *(run harness)* |
| Latency p50 | N/A | *(run harness)* |
| Latency p95 | N/A | *(run harness)* |

> **Note on old MRR=0.25:** Computable from the table in `ground_truth_top3.md`:
> - Q2: first hit (building-native-ui) at rank 2 → RR = 0.50
> - Q9: first hit (design-system-patterns) at rank 1 → RR = 1.00
> - Q10: first hit (wireframe-prototyping) at rank 1 → RR = 1.00
> - All others: 0
> - MRR = (0.50 + 1.00 + 1.00) / 10 = **0.25**

### 3.2 Per-query breakdown

*(Populated by running `python test_cases/eval_harness.py`)*

| QID | Query (truncated) | P@1 | P@3 | MRR | NDCG@3 | p50ms | p95ms |
|-----|-------------------|-----|-----|-----|--------|-------|-------|
| q01 | build ios app with swift and firebase… | — | — | — | — | — | — |
| q02 | react native expo push notifications… | — | — | — | — | — | — |
| q03 | summarize long research papers | — | — | — | — | — | — |
| q04 | clean csv data and generate statistica… | — | — | — | — | — | — |
| q05 | convert pdf to structured markdown… | — | — | — | — | — | — |
| q06 | generate blog post from bullet points… | — | — | — | — | — | — |
| q07 | automate github issue triage using ai… | — | — | — | — | — | — |
| q08 | deploy dockerized fastapi app to aws… | — | — | — | — | — | — |
| q09 | build scalable design system with reusa… | — | — | — | — | — | — |
| q10 | generate figma ui wireframes from produ… | — | — | — | — | — | — |
| q11 | write unit tests for typescript react… | — | — | — | — | — | — |
| q12 | perform code review to find security… | — | — | — | — | — | — |
| q13 | set up kubernetes cluster with helm… | — | — | — | — | — | — |
| q14 | implement gitops workflow with argocd… | — | — | — | — | — | — |
| q15 | write email sequence for saas product… | — | — | — | — | — | — |
| q16 | repurpose youtube video transcript… | — | — | — | — | — | — |
| q17 | track user analytics events and convers… | — | — | — | — | — | — |
| q18 | improve my code | — | — | — | — | — | — |
| q19 | help me with my project | — | — | — | — | — | — |
| q20 | write a business email responding… | — | — | — | — | — | — |

---

## 4. Qualitative Human Evaluation

### 4.1 Rubric

| Score | Label | Description |
|-------|-------|-------------|
| **2** | Highly relevant | Directly addresses the query. User would install it immediately. |
| **1** | Partially relevant | Related, might be useful, but not the obvious choice. |
| **0** | Not relevant | User would be confused seeing this result. |

### 4.2 Procedure

1. Each team member independently rates the 3 returned results for each of the 10 original queries (30 ratings per person).
2. Record ratings in `docs/human_ratings.csv` (columns: rater, query_id, rank, skill_id, score).
3. Compute inter-rater agreement with Cohen's Kappa (target κ > 0.6).
4. Average ratings across raters → Mean Relevance Score per query.

### 4.3 Results

*(Fill in after human rating session)*

| Query | Rater A | Rater B | Rater C | Mean | Cohen's κ |
|-------|---------|---------|---------|------|-----------|
| q01 | — | — | — | — | — |
| q09 | — | — | — | — | — |
| q10 | — | — | — | — | — |
| … | | | | | |

---

## 5. Recommender Evaluation

### 5.1 Proxy evaluation

Since there is no ground truth for recommendations, three synthetic scenarios are defined in `test_cases/recommend_scenarios.json`. Each scenario has `fake_prompts` (simulated recent conversation messages) and `expected_skills`.

| Scenario | Description | Expected skills |
|----------|-------------|----------------|
| s01 ios-firebase | iOS app + Firebase auth | swiftui-expert-skill, mobile-ios-design, auth-implementation-patterns |
| s02 devops-kubernetes | K8s microservices deployment | kubernetes-specialist, helm-chart-scaffolding, gitops-workflow |
| s03 content-creator | Multi-channel content repurposing | content-repurposer, email-sequence, seo-geo |

**Scoring:** P@3 using the same binary precision formula as search eval.

### 5.2 Results

*(Fill in after running recommend evaluation)*

| Scenario | P@3 | Returned skills |
|----------|-----|----------------|
| s01 ios-firebase | — | — |
| s02 devops-kubernetes | — | — |
| s03 content-creator | — | — |

---

## 6. Error Analysis

*(Complete after running the harness — identify 5 worst queries by NDCG@3)*

**Common failure modes to look for:**

1. **Corpus gap** — The ideal skill doesn't exist (e.g., Q4 csv/pandas). The only fix is expanding the corpus.
2. **Embedding mismatch** — Query terms don't align with how skills describe themselves (e.g., "triage" vs "categorize issues").
3. **Ambiguous query** — Multiple valid interpretations; retriever picks the wrong one (e.g., Q18 "improve my code").
4. **Popularity bias** — Widely-used generic skills surface over niche but correct ones.
5. **Description quality** — Some skill descriptions in the corpus are sparse (e.g., `github-issue-triage` has an empty description), hurting vector similarity.

---

## 7. Framing the Numbers

**Random baseline:** P@3 = 3/921 ≈ **0.003**

If mean P@3 ≥ 0.20 with the validated ground truth, SkillRank is approximately **67× better than random**.

**The validated GT is more honest than the original:** The original P@3=0.20 was misleadingly low because 23/30 expected skills don't exist in the corpus — the system couldn't possibly match them. With validated ground truth, P@3 reflects actual retrieval quality against achievable targets.

**What P@3=0.20 tells us on validated GT:** 20% of top-3 results are directly relevant — meaning typically 0–1 hit per query. There is significant room for improvement via query expansion, better skill descriptions, or cross-encoder reranking.

---

## 8. Running the Eval

```bash
# Prerequisites: backend + Qdrant must be running
# See docs/HOW_TO_RUN.md

# Run evaluation (from repo root)
python test_cases/eval_harness.py

# With options
python test_cases/eval_harness.py --base-url http://localhost:8000 --top-k 5

# Results written to test_cases/results/eval_<timestamp>.json
# Exit code 1 if mean P@3 < 0.15 (regression gate)
```

### Sanity checks after running

- Q9 (design system): expect P@3 ≥ 0.67 — `design-system-patterns` and `web-component-design` are strong exact matches.
- Q10 (figma wireframes): expect P@3 ≥ 0.67 — `wireframe-prototyping` and `implement-design` are strong matches.
- Latency p50 should be < 500ms on local setup.
- Script exits 0 (pass) if mean P@3 ≥ 0.15.
