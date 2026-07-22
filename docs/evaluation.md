# Evaluation

Both halves of the pipeline — retrieval, and the final LLM answer — are evaluated with more than one approach, against the same LLM-generated ground truth set.

**The outputs are committed to the repo** — `data/evaluation/ground_truth.csv`, `rag_answers.csv`, and `version_blending_evaluations.csv` are all checked in, so you can inspect the actual questions, answers, and judgments directly without running anything or spending API budget. The sections below describe what each script does and which committed file to open for its output; see [setup.md](setup.md#running-the-evaluation-suite) if you want to regenerate them yourself instead.

## 1. Ground truth generation — `evaluation/01_generate_ground_truth.py`

Since there's no pre-existing Q&A dataset for "migrating FastAPI/Pydantic/SQLAlchemy code," ground truth is generated with an LLM:

- A stratified sample of chunks is drawn from the knowledge base: 17 FastAPI, 17 Pydantic, and 16 SQLAlchemy chunks (50 total), restricted to chunks with more than 40 words so there's enough substance to write a question from.
- For each sampled chunk, `gpt-5.4-mini` is prompted (with structured output, a `Questions` Pydantic model) to generate **5 realistic migration questions** answerable *only* from that chunk — explicitly "how do I rewrite this old code" style questions rather than conceptual "what changed" questions, per the few-shot examples in the prompt.
- Output: `data/evaluation/ground_truth.csv` with `question`, `document` (the source chunk id), and `library` columns — up to 250 question/answer-source pairs. **Committed to the repo** — open it directly to see the actual generated questions.

## 2. Retrieval evaluation — `evaluation/02_evaluate_search.py`

For every ground-truth question, each retrieval strategy is asked for its top 5 results, filtered to the question's library. A result counts as a **hit** if it comes from the same source *file* as the chunk the question was generated from (matched at the file level, i.e. ignoring the specific sub-chunk number — a question can be legitimately answered by a neighboring chunk from the same doc page).

Two metrics are computed:

- **Hit Rate@5** — fraction of questions where at least one of the top 5 results is a hit
- **MRR@5** — mean reciprocal rank of the first hit (rewards putting the right document *first*, not just somewhere in the top 5)

Strategies compared:

| Strategy | Description |
|---|---|
| Keyword only | BM25 over the SQLite FTS5 index |
| Vector only | Cosine similarity over MiniLM embeddings |
| Hybrid (1:1, 2:1, 5:1, 10:1) | RRF fusion of both, swept across keyword:vector weight ratios |

The best-performing ratio from this sweep is what's hardcoded as the default in `HybridSearcher.__init__` (`kw_weight` / `vec_weight` in `src/hybrid_search.py`) — the comment above the class (`# To reflect Evaluation results, default weights...`) records that this default was chosen from these results, not guessed.

This script only prints to stdout — its results aren't saved to a CSV, so unlike the sections below there's no committed file to inspect directly. It's local-only (BM25 + embeddings, no LLM calls), so it's free and fast to run yourself:

```bash
python evaluation/02_evaluate_search.py
```

Paste your own run's numbers into a table here for the record, e.g.:

| Strategy | Hit Rate@5 | MRR@5 |
|---|---|---|
| Keyword only (BM25) | _fill in_ | _fill in_ |
| Vector only | _fill in_ | _fill in_ |
| Hybrid (1:1) | _fill in_ | _fill in_ |
| Hybrid (2:1) | _fill in_ | _fill in_ |
| Hybrid (5:1) | _fill in_ | _fill in_ |
| Hybrid (10:1) | _fill in_ | _fill in_ |

## 3. RAG vs. baseline answers — `evaluation/03_evaluate_rag.py`

For every ground-truth question, two answers are generated in parallel (10 worker threads):

- **RAG answer** — through the full `MigrationAssistant.answer_question()` pipeline (hybrid retrieval + system prompt + context), filtered to the question's library
- **Baseline answer** — the same LLM (`gpt-5.4-mini`) answering the raw question directly, with no retrieved context and no system prompt

The run is resumable: it loads any existing `data/evaluation/rag_answers.csv`, skips questions already answered, and only processes what's left — so a failed or interrupted run doesn't cost you a full re-run of the API calls. Output columns: `question`, `answer_llm` (RAG), `answer_baseline`, `answer_orig` (the source chunk's raw text, for reference), `document`. **Committed to the repo** — open `rag_answers.csv` directly to compare RAG vs. baseline answers side by side for every ground-truth question.

## 4. LLM-as-judge: modern-syntax compliance — `evaluation/04_llm_judge.py`

Domain-specific eval metric: does the **recommended** solution in an answer still rely on legacy/deprecated syntax (e.g. Pydantic v1 `@validator`, SQLAlchemy 1.x `session.query()`)?

Both the RAG answer and the baseline answer for every question are independently judged by `gpt-5.4-mini` with structured output (`BlendingEvaluation`: a `reasoning` string plus a `contains_legacy_syntax` boolean). The judge prompt explicitly allows "Before/After" comparisons — legacy syntax shown as the *old* version is fine; it's only flagged if the actual recommended answer is the outdated one.

This gives a **modern-syntax compliance rate** for baseline vs. RAG-assisted answers:

```
compliance % = 100 - (% of answers flagged as containing legacy syntax)
```

`python evaluation/04_llm_judge.py` writes `data/evaluation/version_blending_evaluations.csv` — **committed to the repo** — with per-question reasoning and verdicts for both the baseline and RAG answers, plus a printed summary table of the aggregate compliance rates:

| | Modern-syntax compliance | Outdated-syntax rate |
|---|---|---|
| Baseline (no RAG) | see `version_blending_evaluations.csv` | |
| RAG-assisted | see `version_blending_evaluations.csv` | |

This is the headline number for the project: it directly measures whether retrieval-augmentation reduces the "confidently recommends deprecated code" failure mode the assistant was built to fix. If you'd rather have the aggregate percentages inline here instead of pointing at the CSV, compute them once from your run and replace this table with the actual numbers.
