# Usage

## The Assistant (`app.py`)

Once running, `http://localhost:8501` shows:

1. **Target Library** — a sidebar filter (`All`, `fastapi`, `pydantic`, `sqlalchemy`). Restricting to one library narrows retrieval to that library's chunks only, which helps when the same term means different things across frameworks.
2. **Question** — describe what you're migrating, ideally mentioning the versions involved, e.g.:
   > I'm migrating my data models from Pydantic v1 to v2. How do I rewrite my old @validator methods to the new Pydantic v2 syntax?
3. **Paste your old code (optional)** — paste the legacy snippet you want rewritten. It's passed to the LLM alongside the retrieved documentation, so the answer can reference your actual code rather than a generic example.
4. **Generate Guide** — runs hybrid retrieval (top 5 chunks) and sends the question, retrieved docs, and your code to the LLM.

The response includes:

- The answer itself, with the modernized code only (the system prompt explicitly forbids showing deprecated syntax as the recommended solution)
- Response time, cost, and token usage for that single call
- An expandable list of the retrieved documentation chunks (library, version, heading, filename) so you can verify the answer against the source
- 👍 / 👎 feedback buttons, tied to that conversation's ID

If no relevant chunks are retrieved, the app tells you rather than letting the LLM guess — try removing the library filter, rephrasing without specific version numbers, or using different keywords.

### Example walkthrough

1. Select `pydantic` as the target library.
2. Ask: *"How do I migrate my old Pydantic v1 `@validator('name')` method to the new Pydantic v2 syntax?"*
3. Paste the old validator code, if you have it.
4. Click **Generate Guide** and review the modernized code plus the cited Pydantic v2 doc sections.
5. Click 👍 or 👎 to log feedback — this shows up in the telemetry dashboard.

## The Telemetry Dashboard (`dashboard.py`)

`http://localhost:8502` reads from the same monitoring database and shows:

- **Top-level metrics:** total conversations, average response time, total cost, and average tokens per conversation
- **Usage charts:** cost over time, response time over time, per-library request volume, token usage distribution, and feedback score distribution
- **Recent activity:** the 10 most recent conversations, including a question preview, response time, cost, and the library selected for retrieval

The dashboard is populated automatically as people use the assistant—there's no separate ingestion step. Every question asked through `app.py` writes a conversation record to `data/processed/monitoring.db`, and every 👍/👎 feedback submission is stored as a linked feedback record, which is reflected in the dashboard.

## Recording a demo


