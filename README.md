# Python Migration Assistant

A RAG-powered assistant that helps developers upgrade **FastAPI**, **Pydantic**, and **SQLAlchemy** code to their latest major versions — grounded in the official docs and release notes instead of a general-purpose LLM's (often outdated) training data.

> Built as a course capstone project: end-to-end ingestion → hybrid retrieval → LLM answer generation → evaluation → UI → monitoring, all containerized.

## Problem

Framework upgrades like Pydantic v1 → v2, SQLAlchemy 1.x → 2.0, and the various FastAPI releases change core APIs (validators, `Depends()` + `Annotated`, `session.query()` vs. the new `select()` style, and so on). Generic LLMs are frequently trained on a mix of old and new syntax and will confidently recommend deprecated patterns, or blend old and new APIs in the same answer.

**Python Migration Assistant** answers migration questions by retrieving the *actual, version-specific* documentation and release notes for the library in question, and instructs the LLM to only use modernized syntax supported by that retrieved context — optionally rewriting a pasted code snippet directly. Every claim is traceable back to a specific library, version, and doc section.

The knowledge base is built from official project documentation and GitHub release notes for FastAPI, Pydantic, and SQLAlchemy — not the Zoomcamp FAQ dataset.

## Docs

| Doc | Covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | How the pipeline works end to end, a diagram, project structure, and the tech stack |
| [docs/setup.md](docs/setup.md) | Prerequisites, environment variables, running locally with `uv`, running with Docker Compose, building the knowledge base |
| [docs/usage.md](docs/usage.md) | Walkthrough of the assistant UI and the telemetry dashboard |
| [docs/evaluation.md](docs/evaluation.md) | Ground-truth generation, retrieval evaluation, RAG-vs-baseline LLM-judge methodology, and how to reproduce results |

## Quickstart

```bash
git clone <your-repo-url> python-migration-assistant
cd python-migration-assistant
cp .env.example .env   # add OPENAI_API_KEY (and optionally GITHUB_TOKEN)

docker compose up --build
```

Then open:
- `http://localhost:8501` — the assistant
- `http://localhost:8502` — the telemetry dashboard

The first run needs the knowledge base to exist. If `data/processed/chunks.json` isn't already present, build it first — see [docs/setup.md](docs/setup.md#building-the-knowledge-base) for the one-command ingestion pipeline.

## Where this maps to the grading rubric

| Criterion | What satisfies it |
|---|---|
| Problem description | See [Problem](#problem) above |
| Retrieval flow | Knowledge base (hybrid search over docs + release notes) **and** an LLM are both used — `src/hybrid_search.py`, `src/rag.py` |
| Retrieval evaluation | Multiple retrieval approaches evaluated (keyword-only, vector-only, 4 hybrid weightings); best one is the shipped default — `evaluation/02_evaluate_search.py` |
| LLM evaluation | Multiple approaches evaluated (RAG vs. no-context baseline) via an LLM-judge metric — `evaluation/03_evaluate_rag.py`, `evaluation/04_llm_judge.py` |
| Interface | Streamlit web UI — `app.py` |
| Ingestion pipeline | Automated with a single script, `scripts/build_dataset.py` (chains docs download → release notes → chunk → embed → index). No dedicated orchestrator (Airflow/Prefect/Kestra) is used yet — see [Possible improvements](#possible-improvements) |
| Monitoring | Feedback (👍/👎) is collected **and** there's a dashboard (`dashboard.py`) with KPI cards and time-series charts. Currently 2 charts + 4 metric cards; see [Possible improvements](#possible-improvements) for getting to 5+ charts |
| Containerization | Full `docker-compose.yml` covering both services (assistant + dashboard) |
| Reproducibility | Pinned dependencies via `uv.lock`; dataset is deterministically rebuildable from pinned GitHub branches/tags + the Releases API; `data/evaluation/*.csv` is committed so reviewers can inspect ground truth, RAG-vs-baseline answers, and judge verdicts without spending API budget — see [docs/setup.md](docs/setup.md) |
| Best practice: hybrid search | Implemented and evaluated — `src/hybrid_search.py`, `evaluation/02_evaluate_search.py` |
| Best practice: re-ranking | Not implemented |
| Best practice: query rewriting | Not implemented |
| Bonus: cloud deployment | Not implemented (local Docker Compose only) |

## Possible improvements

- Swap the plain-script pipeline in `scripts/build_dataset.py` for an orchestrator (Airflow, Prefect, or Kestra) for scheduled/incremental re-ingestion.
- Add more charts to `dashboard.py` — e.g. conversations per library, feedback score distribution, retrieval hit-rate over time, token cost breakdown by model — to round out the monitoring story.
- Add a cross-encoder re-ranking step after hybrid retrieval.
- Add query rewriting/expansion ahead of retrieval (useful for short or ambiguous questions).
- Deploy to a cloud target (e.g. a managed container service) instead of local Docker Compose only.

## License

Add your license of choice here.
