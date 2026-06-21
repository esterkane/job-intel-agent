# Job Intel Agent

Local-first job intelligence for Brian, an Elastic Support Engineer in Germany moving toward strategic roles in AI search, RAG, knowledge systems, support workflow modernization, technical advisory work, and agentic workflows.

The app discovers, ranks, explains, and helps prepare for jobs. It does **not** auto-apply, submit forms, bypass CAPTCHAs, scrape behind login, use fake accounts, rotate proxies, or require paid APIs.

## What It Does

- Ingests allowed public/API job sources from `config/job_platforms.yaml`.
- Keeps restricted platforms in manual-assist mode.
- Normalizes jobs into PostgreSQL and deduplicates by company, title, location, URL, and content hash.
- Scores jobs from 0-100 with deterministic local logic focused on AI search, RAG, knowledge systems, agentic workflows, and Elastic background fit.
- Enforces strict location logic: remote Germany and remote EU/EMEA are preferred; US-only, Canada-only, UK-only, London, Amsterdam, onsite-only, and relocation-required roles are penalized or filtered.
- Provides a React dashboard for jobs, source health, scrape status, notes, status updates, and manual capture.
- Provides a Browser Assistant for safe manual review of login-heavy platforms.

## What It Does Not Do

- No auto-apply.
- No credential scraping or authenticated job-board scraping.
- No stealth scraping, CAPTCHA bypass, fake accounts, or proxy rotation.
- No aggressive crawling.
- No required OpenAI API usage.
- No automatic application submission or form filling.

## Cost Model

The core app runs locally with Docker, PostgreSQL, FastAPI, React, Playwright, and deterministic scoring. It does not require OpenAI or any paid API.

Ollama is optional and local. OpenAI is optional, disabled by default, and may create separate API billing costs. ChatGPT Pro does not include free API usage.

## Quick Start

```bash
cd job-intel-agent
copy .env.example .env
docker compose up --build
```

Open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Optional profiles:

```bash
docker compose --profile vector up --build
docker compose --profile llm up --build
```

## Platform Sources

`config/job_platforms.yaml` uses these categories:

- `api_json`: API/feed-first sources. Arbeitnow and Working Nomads are enabled by default.
- `public_static`: public unauthenticated pages fetched politely with `httpx`.
- `public_playwright`: public unauthenticated JavaScript pages opened with Playwright.
- `rss_or_feed`: reserved for feed-first sources.
- `jobspy_optional`: disabled by default; use only where allowed and at low volume.
- `manual_browser_only`: saved-search/manual capture only.
- `disabled_due_to_terms`: visible as a reference but never scraped.

Manual-only sources include LinkedIn, Indeed, Glassdoor, FlexJobs, Wellfound, PowerToFly, and XING. Use saved searches, job alerts, or the Manual Capture page. The app never automates bulk extraction from logged-in or restricted pages.

## Browser Assistant

The Browser Assistant has three safe workflows:

- Saved Search Launcher: the app stores search URLs and opens them in your browser. You review results manually; the app does not scrape logged-in result pages.
- Manual Job Capture: paste URL, title, company, location, and description. The backend normalizes, deduplicates, scores, and stores the job with `source_type=manual_capture` and `ingestion_method=manual_capture`.
- Optional Browser Session: hidden unless a source is explicitly configured as `source_type: browser_allowed`. Login is initiated manually by the user in a visible browser, credentials are never stored by the app directly, and extraction is limited to sources where permission has been checked.

Seeded saved searches live in `config/saved_searches.yaml`. You can add/edit/delete saved searches from the Browser Assistant page or via `/api/saved-searches`.

Logged-in scraping is disabled by default because many job platforms restrict automated extraction. To add a browser-allowed source, first review the platform terms and robots guidance, document the decision in `config/job_platforms.yaml` under `tos_review`, then change the source to `browser_allowed`. Do not use this for LinkedIn, Indeed, Glassdoor, FlexJobs, Wellfound, PowerToFly, XING, StepStone, or Instaffo unless you have explicit permission for the intended use.

## Run A Scrape

From the UI:

- Dashboard: run all enabled sources.
- Sources: run one source.
- Use Fresh overwrite to remove old unsaved imported jobs before re-ingesting. Saved and applied jobs are preserved.

From the API:

```bash
curl -X POST http://localhost:8000/api/scrape/run
curl -X POST "http://localhost:8000/api/scrape/run?fresh=true"
curl -X POST http://localhost:8000/api/scrape/run/1
```

The worker also schedules a daily scrape at `DAILY_SCRAPE_TIME`, default `07:00 Europe/Berlin`.

## Manual Capture

Use the Manual Capture page for restricted platforms or jobs found in saved-search emails. Paste title, company, URL, location/remote policy, and description. The backend scores and saves the job locally.

## Tune Scoring

Edit `config/search_profile.yaml`:

- `search_phrases`
- `keyword_groups.positive_core`
- `keyword_groups.positive_background_fit`
- `keyword_groups.negative`
- `target_location_logic`
- `scoring_weights`

The scoring model is deterministic and transparent. It does not need an LLM.

## Ollama

Ollama is disabled by default.

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b
```

Start with:

```bash
docker compose --profile llm up --build
```

Pull a model inside the Ollama container if needed:

```bash
docker compose exec ollama ollama pull llama3.1:8b
```

## OpenAI

OpenAI is disabled by default and is never required for scraping, ranking, dashboard use, or basic summaries.

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

Using OpenAI API may create separate API billing costs.

## Legal And Ethical Scraping

- Respect robots.txt and site terms where applicable.
- Prefer official APIs, RSS feeds, or ATS endpoints when available.
- Do not bypass CAPTCHAs.
- Do not scrape behind authentication.
- Do not use proxy rotation, fake accounts, or stealth techniques.
- Keep crawling polite and low-volume.
- Do not auto-apply to jobs.

## Agent Access (MCP)

A **read-only** [Model Context Protocol](https://modelcontextprotocol.io) server
exposes the job-intelligence core as agent tools, so an MCP client (Claude Code,
Cursor, a LangGraph agent) can query scored jobs and configured sources without
the HTTP API or a browser. The tools are **thin adapters** over the existing
`backend/` functions and are strictly read-only — no scrape-run, ingest, or
mutation is exposed.

Tools: `search_jobs(query?, filters?)`, `get_job(job_id)`, `list_sources()`.

Run it (working dir `backend/`):

```bash
cd backend
pip install -e ".[test]"
python -m app.mcp.server     # stdio transport (default); MCP_TRANSPORT=http for HTTP
```

See [`docs/mcp.md`](docs/mcp.md) for the tool reference, the structured-error
contract, response shapes, and client registration.

## Development

Backend tests:

```bash
cd backend
pip install -e ".[test]"
pytest
```

Frontend build:

```bash
cd frontend
npm install
npm run build
```

More detail lives in `docs/`.
