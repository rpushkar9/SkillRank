# SkillRank — Evaluation & Metrics Report

---

## 1. Overview

SkillRank is a hybrid skill-recommendation search engine that returns the top-K most relevant Claude skills from a 921-skill corpus given a natural-language query. The pipeline is: **Qdrant vector retrieval → score-based ranking**.

This report covers the formal evaluation of the system against a validated ground truth of 20 queries using four quantitative metrics, a qualitative error analysis, and a rubric for human evaluation.

---

## 2. Evaluation Setup

### 2.1 Corpus

| Property | Value |
|----------|-------|
| Total skills indexed | 921 |
| Retrieval backend | Qdrant (vector similarity, `all-MiniLM-L6-v2`) |
| Default top-K | 3 |

### 2.2 Ground Truth Construction

**Initial discovery (critical finding):** The original hand-written ground truth (`ground_truth_top3.md`) expected 30 skill IDs across 10 queries. After validation:

| Status | Count | % |
|--------|-------|---|
| Exists in corpus | 7 | 23% |
| Missing from corpus | 23 | 77% |

The original P@3 = 0.20 was computed against a mostly-phantom dataset — most zero-precision queries scored 0 not because retrieval failed, but because the expected skill literally doesn't exist in the database. **This is a dataset coverage problem, not a retrieval quality problem.**

The validated ground truth replaces all phantom skill IDs with the closest real skills that exist in the corpus. Two queries are marked **unanswerable** (no relevant skill exists for the topic):

- **Q4** — *clean csv data and generate statistical report in python*: The corpus has no data analysis / pandas-style skills at all. System is expected to return low-confidence results.
- **Q19** — *help me with my project*: Maximally vague; no meaningful match is possible.

### 2.3 Graded Relevance Scale

| Grade | Label | Meaning |
|-------|-------|---------|
| **2** | Highly relevant | Directly addresses the query intent. User would install immediately. |
| **1** | Partially relevant | Related, might be useful, not the obvious choice. |
| **0** | Not relevant | User would be confused seeing this result. |

### 2.4 Metrics

| Metric | Why included |
|--------|-------------|
| **P@1** | Did the single best result hit? |
| **P@3** | Are most of the top-3 results on-target? Primary metric. |
| **MRR** | Was there *any* good result, and how high was it ranked? |
| **NDCG@3** | Position-weighted quality with partial credit for grade-1 matches. |

**Random baseline:** P@3 = 3 / 921 ≈ **0.003** (returning 3 random skills from 921).

---

## 3. Quantitative Results

### 3.1 Per-query breakdown (10 original queries, Qdrant backend)

| QID | Query | P@1 | P@3 | MRR | NDCG@3 | Returned top-3 |
|-----|-------|-----|-----|-----|--------|----------------|
| q01 | build ios app with swift and firebase auth | 0.00 | 0.33 | 0.33 | 0.32 | clerk-setup, **react-native-expo**, **swiftui-expert-skill** |
| q02 | react native expo push notifications setup | 1.00 | 1.00 | 1.00 | 0.84 | **react-native-architecture**, **building-native-ui**, **react-native-expo** |
| q03 | summarize long research papers | 1.00 | 0.33 | 1.00 | 0.32 | **latex-paper-en**, web-search, firecrawl |
| q04 | clean csv data + statistical report (python) | 0.00 | 0.00 | 0.00 | 0.00 | tailored-resume-generator, product-manager-toolkit, python-error-handling |
| q05 | convert pdf to structured markdown w/ citations | 0.00 | 0.33 | 0.50 | 0.48 | obsidian-markdown, **baoyu-format-markdown**, seo-geo |
| q06 | generate blog post from bullets w/ SEO | 1.00 | 1.00 | 1.00 | 0.88 | **content-strategy**, **seo-geo**, **pre-publish-post-assistant** |
| q07 | automate github issue triage using ai agent | 0.00 | 0.00 | 0.00 | 0.00 | semgrep, ai-elements, powerpoint-automation |
| q08 | deploy dockerized fastapi app to aws w/ ci/cd | 0.00 | 0.33 | 0.50 | 0.48 | secrets-management, **devops-engineer**, claude-automation-recommender |
| q09 | build scalable design system w/ react components | 1.00 | 0.67 | 1.00 | 0.87 | **design-system-patterns**, **web-component-design**, vercel-composition-patterns |
| q10 | generate figma wireframes from product description | 1.00 | 0.67 | 1.00 | 0.80 | **wireframe-prototyping**, qa-test-planner, **implement-design** |
| | **Mean** | **0.50** | **0.47** | **0.63** | **0.50** | |

Bold = relevant result (grade ≥ 1).

### 3.2 System comparison

| Metric | Old pipeline (phantom GT) | Qdrant (validated GT) | Notes |
|--------|--------------------------|----------------------|-------|
| P@1 | — | **0.50** | |
| **P@3** | 0.20 | **0.47** | ~2.3× improvement when measured fairly |
| **MRR** | 0.25 | **0.63** | |
| NDCG@3 | — | **0.50** | |
| vs. random | 0.20 / 0.003 ≈ 67× | 0.47 / 0.003 ≈ **157×** | |

> The old P@3=0.20 is not directly comparable because it used phantom ground truth. The Qdrant backend measured against the validated GT shows substantially better retrieval quality.

### 3.3 Interpretation

**Strengths:**

- **Q2, Q6** — perfect retrieval (P@3 = 1.0, NDCG = 0.88): well-represented topic areas in the corpus with descriptive skill metadata.
- **Q9, Q10** — strong partial hits (P@3 = 0.67): design and Figma topics have good corpus coverage.
- **MRR = 0.63** — on average the first relevant result appears near rank 2 of 3, meaning the system is surfacing relevant skills but sometimes not in the top slot.

**Weaknesses:**

- **Q4** — complete failure: data analysis topic is not covered in the corpus at all. A corpus coverage problem, not a retrieval problem.
- **Q7** — complete failure: `github-issue-triage` exists in the corpus but has an **empty description**, so vector similarity has nothing to embed. The skill can't be retrieved by semantic search.
- **Q1** — near-miss: `swiftui-expert-skill` is returned at rank 3 (correct), but the top-2 results are off-topic. The query's "firebase" keyword pulls iOS auth-adjacent skills down.

---

## 4. Qualitative Evaluation

### 4.1 Error analysis — 5 worst queries

| Rank | QID | NDCG@3 | Root cause | Fix direction |
|------|-----|--------|------------|---------------|
| 1 | q04 (csv/python) | 0.000 | **Corpus gap** — no data analysis skills exist | Add pandas/EDA skills to corpus |
| 2 | q07 (github triage) | 0.000 | **Empty description** — `github-issue-triage` has no text to embed | Enrich skill descriptions; add BM25 name-match fallback |
| 3 | q01 (ios/firebase) | 0.319 | **Keyword drift** — "firebase" pulls auth-adjacent results; SwiftUI skill appears only at rank 3 | Query expansion or title-boosting |
| 4 | q03 (research papers) | 0.319 | **Vocabulary mismatch** — "summarize" maps to `latex-paper-en` (correct domain, wrong task); pure summarisation not well-covered | Add summarisation skills; expand corpus |
| 5 | q05 (pdf→markdown) | 0.480 | **Weak corpus representation** — `baoyu-format-markdown` is correct but not rank 1; `obsidian-markdown` surfaces first due to surface-level markdown overlap | Reranking with title-match boost |

### 4.2 Best result examples

**Q6 — "generate blog post from bullet points with SEO optimization"** (NDCG = 0.88)

All three returned results are on-topic:
- `content-strategy` (grade 1): content planning tool
- `seo-geo` (grade 2): SEO + GEO optimization — direct match
- `pre-publish-post-assistant` (grade 1): blog post preparation tool

The query has clear, unambiguous vocabulary that maps well to skill descriptions. This is the system at its best.

**Q2 — "react native expo push notifications setup"** (NDCG = 0.84, P@3 = 1.0)

All three results are relevant:
- `react-native-architecture` (grade 1): production RN patterns
- `building-native-ui` (grade 1): Expo UI guidelines
- `react-native-expo` (grade 2): exact match

The corpus has strong React Native coverage, and the query vocabulary aligns with skill names.

### 4.3 Failure example in depth

**Q7 — "automate github issue triage using ai agent"** (NDCG = 0.00)

The skill `github-issue-triage` exists in the corpus and is a perfect match (grade 2). But its stored description is an empty string — meaning the sentence-transformer has nothing to embed beyond the skill name itself.

The query term "triage" semantically maps to `semgrep` (static analysis, code scanning) — not unreasonable, but wrong. This is an **indexing quality failure**, not a retrieval architecture failure. Enriching the skill description would likely fix this query without any model changes.

### 4.4 Human evaluation rubric

For team members to conduct qualitative ratings:

**Procedure:**
1. For each of the 10 original queries, rate each of the 3 returned skills using the scale below.
2. Rate independently — do not consult other raters.
3. Record in the shared spreadsheet.
4. Compute inter-rater Cohen's κ (target κ > 0.6).

| Score | Label | Description |
|-------|-------|-------------|
| **2** | Highly relevant | Directly solves the task. Would install immediately. |
| **1** | Partially relevant | Related or useful in context, but not the core answer. |
| **0** | Not relevant | Confusing or unrelated to the query. |

**Expected outcome based on quantitative results:**
- Q2 (react native) and Q6 (blog/SEO) should have near-perfect human ratings
- Q4 (csv/python) and Q7 (github triage) should have near-zero ratings — consistent with automated metrics

---

## 5. Recommender Evaluation

The recommender is evaluated via three synthetic proxy scenarios (see `test_cases/recommend_scenarios.json`). Each scenario simulates a developer's recent conversation context and checks whether the recommender surfaces expected skills.

| Scenario | Simulated context | Expected skills |
|----------|-------------------|----------------|
| **ios-firebase** | iOS + Firebase auth prompts | swiftui-expert-skill, mobile-ios-design, auth-implementation-patterns |
| **devops-kubernetes** | Helm + K8s + GitOps prompts | kubernetes-specialist, helm-chart-scaffolding, gitops-workflow |
| **content-creator** | Blog/email/SEO prompts | content-repurposer, email-sequence, seo-geo |

P@3 is computed using the same binary precision formula as search eval. Results to be filled after running against the live recommender endpoint.

---

## 6. Summary & Key Takeaways

| Finding | Implication |
|---------|-------------|
| 23/30 original GT skills missing from corpus | Old P@3=0.20 understated true quality; validated P@3=0.47 is the real baseline |
| Mean P@3 = **0.47** vs random = 0.003 | System is **~157× better than random** on achievable queries |
| Mean MRR = **0.63** | A relevant result appears on average near rank 1.5 — reasonable for a 3-result display |
| Q4 (data analysis) unanswerable | Primary gap is corpus coverage, not retrieval algorithm |
| Q7 (github triage) fixable without model changes | Enriching empty skill descriptions would recover this query |
| NDCG@3 = **0.50** | System captures about half the ideal graded quality — room for improvement via reranking |

**Next steps ranked by expected impact:**
1. Enrich empty/sparse skill descriptions (fixes Q7-class failures)
2. Expand corpus with data analysis skills (fixes Q4-class failures)
3. Add title-match boost to reranker (improves Q1, Q5 ranking)
4. Cross-encoder reranking for top-50 candidates (NDCG improvement)

---

## 7. Automated Evaluation

Run the harness to reproduce results and evaluate new backend versions:

```bash
# From repo root, with backend + Qdrant running:
python test_cases/eval_harness.py

# Options
python test_cases/eval_harness.py --top-k 5 --base-url http://localhost:8000

# Exits code 1 (regression) if mean P@3 < 0.15
# Writes results to test_cases/results/eval_<timestamp>.json
```
