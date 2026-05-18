# Architecture

The app is a local-first Docker Compose stack:

- `frontend`: React, Vite, TypeScript, Tailwind CSS.
- `api`: FastAPI, SQLAlchemy, PostgreSQL.
- `worker`: APScheduler process that runs daily scrapes.
- `postgres`: persistent relational storage.
- `qdrant`: optional vector database under the `vector` profile.
- `ollama`: optional local LLM under the `llm` profile.

Data flow:

1. Sources load from `config/sources.yaml`.
2. Scraper adapters collect raw postings or job-like links.
3. Jobs normalize into a shared schema.
4. Ingestion deduplicates and updates `last_seen_at`.
5. Scoring compares each job against `config/profile.yaml`.
6. The API serves jobs, sources, scrape runs, stats, and profile data.
7. The frontend provides manual review, save, ignore, applied, and notes workflows.

The architecture is intentionally modest. The app uses agent-like components only where useful: source collector, normalizer, scorer, explainer, and notification placeholder.
