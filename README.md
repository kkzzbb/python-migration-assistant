# Python Migration Assistant

A RAG-powered assistant that helps developers upgrade **FastAPI**, **Pydantic**, and **SQLAlchemy** code to their latest major versions using the official documentation and release notes instead of relying on a general-purpose LLM's often outdated training data.

Built end-to-end with automated data ingestion, hybrid retrieval, LLM-powered answer generation, evaluation, a web interface, monitoring, and containerized deployment.

## Problem

Framework upgrades like Pydantic v1 → v2, SQLAlchemy 1.x → 2.0, and the various FastAPI releases change core APIs (validators, `Depends()` + `Annotated`, `session.query()` vs. the new `select()` style, and so on). Generic LLMs are frequently trained on a mix of old and new syntax and will confidently recommend deprecated patterns, or blend old and new APIs in the same answer.

**Python Migration Assistant** answers migration questions by retrieving the *actual, version-specific* documentation and release notes for the library in question, and instructs the LLM to only use modernized syntax supported by that retrieved context (optionally rewriting a pasted code snippet directly). Every claim is traceable back to a specific library, version, and doc section.

The knowledge base is built from official project documentation and GitHub release notes for FastAPI, Pydantic, and SQLAlchemy.

## Docs

| Doc | Covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | How the pipeline works end to end, project structure, and the tech stack |
| [docs/setup.md](docs/setup.md) | Prerequisites, environment variables, running locally with `uv`, running with Docker Compose, building the knowledge base |
| [docs/usage.md](docs/usage.md) | Walkthrough of the assistant UI and the telemetry dashboard |
| [docs/evaluation.md](docs/evaluation.md) | Ground-truth generation, retrieval evaluation, RAG-vs-baseline LLM-judge methodology, and how to reproduce results |

## Quickstart

```bash
git clone https://github.com/kkzzbb/python-migration-assistant.git
cd python-migration-assistant
cp .env.example .env   # add OPENAI_API_KEY (and optionally GITHUB_TOKEN)

docker compose up --build -d
```

Then open:
- `http://localhost:8501` — the assistant
- `http://localhost:8502` — the telemetry dashboard

The repository already includes the generated knowledge base and search indexes, so the application is ready to use after starting the containers. If you'd like to regenerate the dataset from the original documentation sources instead, see [docs/setup.md](docs/setup.md#building-the-knowledge-base).

## Where this maps to the Evaluation Criteria

| Criterion | What satisfies it |
|---|---|
| Problem description | See [Problem](#problem) above |
| Retrieval flow | Knowledge base (hybrid search over docs + release notes) **and** an LLM are both used — `src/hybrid_search.py`, `src/rag.py` |
| Retrieval evaluation | Multiple retrieval approaches evaluated (keyword-only, vector-only, 4 hybrid weightings); best one is the shipped default — `evaluation/02_evaluate_search.py` |
| LLM evaluation | Multiple approaches evaluated (RAG vs. no-context baseline). An LLM judge measures both outdated syntax usage and version blending in the recommended migration solution. |
| Interface | Streamlit web UI — `app.py` |
| Ingestion pipeline | Automated with a single script, `scripts/build_dataset.py` (chains docs download → release notes → chunk → embed → index). No dedicated orchestrator (Airflow/Prefect/Kestra) is used yet — see [Possible improvements](#possible-improvements) |
| Monitoring | Streamlit telemetry dashboard (`dashboard.py`) with  **5 visualizations** (cost over time, response time over time, per-library usage, token usage distribution, feedback score distribution), **4 KPI cards** (total conversations, average response time, total cost, average tokens), plus recent conversation logs |
| Containerization | Full `docker-compose.yml` covering both the assistant application and the monitoring dashboard |
| Reproducibility | Dependencies are pinned via `uv.lock`. The knowledge base can be reproducibly rebuilt using `scripts/build_dataset.py` from pinned documentation versions, and the evaluation outputs (`data/evaluation/*.csv`) are committed so reviewers can inspect the results without rerunning the evaluation or spending API credits. See [docs/setup.md](docs/setup.md). |
| Best practice: hybrid search | Implemented and experimentally evaluated — `src/hybrid_search.py`, `evaluation/02_evaluate_search.py` |
| Best practice: re-ranking | Not implemented |
| Best practice: query rewriting | Not implemented |
| Bonus: cloud deployment | Not implemented (runs locally via Docker Compose) |

## Possible improvements

- Replace the script-based ingestion pipeline (`scripts/build_dataset.py`) with a workflow orchestrator such as Airflow, Prefect, or Kestra to support scheduled and incremental indexing.
- Add retrieval re-ranking (e.g., cross-encoder or reranker model) to improve document relevance.
- Implement query rewriting or query expansion to better handle ambiguous user questions.
- Deploy the application to a managed cloud platform instead of running only through local Docker Compose.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.


