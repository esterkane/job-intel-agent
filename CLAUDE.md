# Job Intel Agent — Claude Code Instructions

Local-first job intelligence for an Elastic Support Engineer targeting AI search /
RAG / knowledge-systems / agentic-workflow roles. The app discovers, deduplicates,
ranks (0-100, deterministic), and explains jobs, plus assists with manual review of
login-heavy platforms. It **never** auto-applies, scrapes behind login, bypasses
CAPTCHAs, uses fake accounts/proxies, or requires paid APIs.

## Run / test commands

Exact commands only. There is **no CI, no Makefile, no linter/type-checker config**
in this repo (no `.github/workflows`, no ruff/mypy/black/flake8 settings). Do not
invent a quality gate — the only automated gate is pytest.

Full stack (Docker):
```bash
cp .env.example .env        # README shows `copy` (Windows); use cp on Unix
docker compose up --build
# Frontend http://localhost:5173 | API docs http://localhost:8000/docs | Health http://localhost:8000/health
docker compose --profile vector up --build   # + Qdrant
docker compose --profile llm up --build       # + Ollama
```

Backend tests (working dir `backend/`):
```bash
cd backend
pip install -e ".[test]"
pytest
```
- Tests run against `sqlite:///:memory:` (set in `tests/conftest.py`); no live
  Postgres/Qdrant/Ollama needed. SQLAlchemy creates tables at startup.

Frontend build / dev (working dir `frontend/`):
```bash
cd frontend
npm install
npm run build     # tsc && vite build  (tsc is the only type-check gate)
npm run dev       # vite --host 0.0.0.0
```

Run a scrape (API):
```bash
curl -X POST http://localhost:8000/api/scrape/run
curl -X POST "http://localhost:8000/api/scrape/run?fresh=true"
curl -X POST http://localhost:8000/api/scrape/run/1
```

## Architecture in 5 lines

1. Docker Compose stack: `frontend` (React/Vite/TS/Tailwind), `api` (FastAPI +
   SQLAlchemy), `worker` (APScheduler daily scrape), `postgres`; optional `qdrant`
   (`vector` profile) and `ollama` (`llm` profile).
2. Pipeline: sources load from `config/*.yaml` → scraper adapters (`backend/app/scrapers/`)
   collect postings → normalize → ingestion dedups & updates `last_seen_at` → scorer
   ranks → API serves jobs/sources/runs/stats → React for review/save/ignore/applied/notes.
3. Scoring (`backend/app/scoring/matcher.py`) is **deterministic** keyword/weight logic
   from `config/search_profile.yaml`; no LLM required.
4. Semantic ranking (sentence-transformers + optional Qdrant) and LLM summaries
   (`backend/app/llm/client.py`, Ollama/OpenAI) are **optional layers** that degrade
   cleanly when unavailable.
5. Persistence: Postgres in prod, SQLite in tests; tables auto-created at startup
   (no Alembic in this MVP — see `docs/limitations.md`).

## Invariants I must never break

1. **Determinism of the scoring/pipeline.** The default scorer
   (`JobScorer` in `backend/app/scoring/matcher.py`) must stay deterministic and
   LLM-free: same job + same `config/search_profile.yaml` → same `final_score` and
   the same `why_this_matches` / `concerns` / `suggested_*` text. Optional semantic
   and LLM layers may only *blend in at light weight* or *enrich*, never gate
   ingestion or replace the deterministic baseline. (This repo's analog of an
   "agent planner": a fixed collector → normalizer → scorer → explainer chain — keep
   it reproducible.)
2. **Quality gate stays green.** `pytest` (run from `backend/`) must pass, and
   `npm run build` (which runs `tsc`) must type-check, before a change is done.
   There is no separate ruff/mypy gate — do not claim one ran.
3. **Provenance on every job.** Every `Job` row must keep its source/origin fields
   populated: `source_name`, `source_type`, `ingestion_method`, `job_url`,
   `content_hash`, `first_seen_at`, `last_seen_at`. Dedup identity is the
   `uq_job_identity` unique constraint (`company`, `title`, `location`, `job_url`)
   plus `content_hash`. Manual-capture jobs must carry
   `ingestion_method=manual_capture`. Do not drop or fabricate these.
4. **No secrets in git.** Secrets live in `.env` (gitignored); document new vars in
   `.env.example`. Never hardcode keys in `docker-compose.yml` (it uses `env_file`).
   `OPENAI_API_KEY` and any tokens must never be committed.

Repo-specific invariants (honor the project's stated ethics):
5. **No prohibited scraping.** Never add auto-apply, authenticated/login scraping,
   CAPTCHA bypass, fake accounts, proxy rotation, stealth, or aggressive crawling.
   Keep `manual_browser_only` / `disabled_due_to_terms` sources out of automation.
   Respect `SCRAPE_POLITE_DELAY_SECONDS` and robots/ToS; new browser-allowed sources
   require a documented `tos_review` in `config/job_platforms.yaml`.
6. **No paid API required.** The core app must run fully locally without OpenAI/any
   paid API. LLM usage stays optional and disabled by default (`LLM_PROVIDER=none`).
7. **Strict location logic** lives in config (`target_location_logic` /
   `search_profile.yaml`); preserve the remote-DE / remote-EU-EMEA preference and the
   US/CA/UK/onsite/relocation penalties rather than hardcoding it elsewhere.

## Definition of done

- `cd backend && pytest` passes.
- `cd frontend && npm run build` type-checks and builds (tsc is the type gate).
- Quality gate / CI: **N/A — no CI in repo**; the pytest + tsc results above are the
  full gate. State this honestly rather than implying a CI run.
- Provenance intact: new/changed jobs keep source/dedup/hash/timestamp fields; dedup
  constraint and `ingestion_method` semantics preserved.
- Determinism preserved: deterministic scorer output unchanged for unchanged input;
  optional LLM/semantic layers remain optional.
- Docs updated when behavior changes (`README.md`, `docs/`), including
  `docs/limitations.md` if a limitation is added or resolved.
- No secrets added; new env vars documented in `.env.example`.
