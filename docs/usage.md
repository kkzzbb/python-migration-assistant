# Usage

## The assistant (`app.py`)

Once running, `http://localhost:8501` shows:

1. **Target Library** — a sidebar filter (`All`, `fastapi`, `pydantic`, `sqlalchemy`). Restricting to one library narrows retrieval to that library's chunks only, which helps when the same term means different things across frameworks.
2. **Question** — describe what you're migrating, ideally mentioning the versions involved, e.g.:
   > I'm migrating a FastAPI project from 0.95 to 0.115. Why is `Depends()` no longer working inside my `Annotated` types?
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

## The telemetry dashboard (`dashboard.py`)

`http://localhost:8502` reads from the same monitoring database and shows:

- Total conversations, average response time, total cost, and average tokens per conversation (top-row metric cards)
- Cost over time and response time over time (line charts)
- The 10 most recent conversations, with question preview, response time, cost, and library

This is populated automatically as people use the assistant — there's no separate step to run; every question asked in `app.py` writes a row to `data/processed/monitoring.db`, and every 👍/👎 writes a linked feedback row.

## Recording a demo

If you want to attach a short walkthrough video to your README: Streamlit has a built-in screen recorder in the app's top-right menu (Settings → Record a screencast). Record a short pass through the example walkthrough above, then drag the resulting file into the GitHub web editor for your README to embed it.
