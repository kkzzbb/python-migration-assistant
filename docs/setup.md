# Setup

## Prerequisites

- Python 3.12 (matches the `Dockerfile` base image)
- [`uv`](https://github.com/astral-sh/uv) for dependency management
- `git` (the ingestion pipeline clones docs directly from GitHub)
- Docker + Docker Compose, if you'd rather not install anything locally
- An OpenAI API key
- (Optional) A GitHub personal access token, to avoid the GitHub API's low unauthenticated rate limit when fetching release notes (part of building the dataset)

## Environment variables

A template is committed at the project root as `.env.example`:

```dotenv
# ==========================================
# ENVIRONMENT VARIABLES TEMPLATE
# ==========================================
# Note to Reviewer: 
# 1. Copy this file and rename it to exactly: .env
# 2. Replace the placeholder below with your actual API key.

OPENAI_API_KEY=your_actual_api_key_goes_here

# Optional (only needed when rebuilding the dataset)
GITHUB_TOKEN=your_github_personal_access_token
```

Copy it and fill in a real key:

```bash
cp .env.example .env
```

`OPENAI_API_KEY` is required — `src/rag.py` and every script under `evaluation/` instantiate `OpenAI()`, which reads it from the environment (loaded via `load_dotenv()`).

`GITHUB_TOKEN` is optional. It is only used by `scripts/fetch_github_data.py` when downloading GitHub release notes, allowing higher GitHub API rate limits. The script also works without a token, subject to GitHub's unauthenticated rate limits.

### Obtaining an OpenAI API key

This project uses the OpenAI Responses API.

1. Create or sign in to your OpenAI account.
2. Visit https://platform.openai.com/api-keys.
3. Create a new secret API key.
4. Copy it into your `.env` file:

```.env
OPENAI_API_KEY=your_api_key_here
```

> **Note:** OpenAI API access is a paid service. Depending on your account, you may need to add billing information or purchase API credits before requests will succeed. Running the application and the evaluation scripts will consume API tokens and may incur charges. The evaluation scripts `01_generate_ground_truth.py`, `03_evaluate_rag.py`, and `04_llm_judge.py` make OpenAI API calls and therefore consume API tokens. The repository includes the generated evaluation CSV files, so reviewers do not need to rerun them unless they want to regenerate the results.

## Option A — run locally with `uv`

> **Note:** The repository already includes the generated knowledge base and search indexes, so you can **skip Step 2** if you simply want to run the application. Run it only if you want to regenerate the dataset from the original documentation sources.

```bash
# 1. Install dependencies (pinned versions from uv.lock)
uv sync

# 2. Build the knowledge base (optional)
uv run python scripts/build_dataset.py

# 3. Run the assistant
uv run streamlit run app.py --server.port=8501

# 4. In a second terminal, run the monitoring dashboard
uv run streamlit run dashboard.py --server.port=8502
```

## Option B — run with Docker Compose

```bash
docker compose up --build -d
```

This builds one image (from the shared `Dockerfile`) and starts two containers from `docker-compose.yml`:

| Service | Port | Command |
|---|---|---|
| `migration-assistant` | 8501 | `streamlit run app.py` |
| `telemetry-dashboard` | 8502 | `streamlit run dashboard.py` |

Both containers mount `./data` as a volume, so the knowledge base, embeddings, and SQLite databases persist on the host and are shared between the two services.

> **Note:** The repository already includes the generated knowledge base and search indexes, so `docker compose up --build -d` is sufficient to start the application. If you want to verify the ingestion pipeline from scratch, remove the generated data first and run:
>
> ```bash
> docker compose run migration-assistant python scripts/build_dataset.py
> ```

## Building the knowledge base

The full ingestion pipeline is a single command:

```bash
python scripts/build_dataset.py
```

This runs, in order:

1. `scripts/download_docs.py` — sparse-clones the `docs/` (or equivalent) folder for each pinned branch/tag of FastAPI, Pydantic (v1 and v2), and SQLAlchemy (1.4 and 2.0) into `data/raw/<library>/<version>/`. Already-downloaded versions are skipped on subsequent runs.
2. `scripts/fetch_github_data.py` — pulls the most recent GitHub releases for each repo into `data/raw/<library>/releases/<library>_releases.md`.
3. `python -m src.chunker` — cleans, splits, and chunks everything in `data/raw/` into `data/processed/chunks.json`.
4. `python -m src.embeddings` — embeds every chunk and writes `data/processed/embeddings.npy` + `embedding_metadata.json`.
5. `python -m src.keyword_search` — builds the BM25 keyword index at `data/indexes/keyword.db`.

Re-running the whole pipeline is safe — already-downloaded doc versions are skipped, and chunking/embedding/indexing always regenerate from scratch from whatever is in `data/raw/`.

## Running the evaluation suite

**You don't have to run this to review the project.** The generated outputs — `data/evaluation/ground_truth.csv`, `rag_answers.csv`, and `version_compliance_evaluations.csv` — are committed to the repo, so you can open them directly to see the ground-truth questions, the RAG vs. baseline answers, and the LLM-judge verdicts without spending any API budget.

If you want to regenerate them yourself, see [evaluation.md](evaluation.md) for what each script does. In short, run them in order once the knowledge base exists:

```bash
python evaluation/01_generate_ground_truth.py   # -> data/evaluation/ground_truth.csv
python evaluation/02_evaluate_search.py          # prints Hit Rate@5 / MRR@5 to stdout, no API calls
python evaluation/03_evaluate_rag.py              # -> data/evaluation/rag_answers.csv
python evaluation/04_llm_judge.py                  # -> data/evaluation/version_compliance_evaluations.csv
```

`01`, `03`, and `04` call the OpenAI API (for ground-truth generation, answer generation, and judging respectively), so re-running them from scratch will incur API costs. `02` is local-only (BM25 + embeddings, no LLM calls) and safe to re-run any time. `03` is resumable — it skips questions already present in `rag_answers.csv`, so deleting just a few rows and re-running only regenerates those. If you delete a committed CSV and re-run its script, you'll overwrite the committed results with your own.

## Stopping the application

If you started the services with Docker Compose, stop and remove the containers with:

```bash
docker compose down
```

The generated data and monitoring database are stored in the mounted `data/` directory, so they remain on your machine and are reused the next time you start the application.