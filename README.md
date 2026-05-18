# Job Intel Agent

Local-first job intelligence for Sanja: daily discovery, ranking, and preparation support for remote-friendly strategic roles in AI agents, RAG/search, customer automation, support workflow modernization, knowledge systems, enablement, developer education, and observability.

This app discovers and ranks jobs. It does **not** auto-apply, bypass CAPTCHAs, scrape behind login, or require paid APIs.

## What It Does

- Keeps a configurable registry of company and job-board sources in `config/sources.yaml`.
- Scrapes a small enabled source set with polite Playwright or static HTML adapters.
- Normalizes jobs into one PostgreSQL schema.
- Deduplicates by company, title, location, URL, and content hash.
- Scores jobs from 0-100 using deterministic local logic tuned to Sanja's profile.
- Explains matches, concerns, CV emphasis, and suggested application angle.
- Provides a React dashboard for jobs, sources, scrape status, notes, and status updates.
- Supports optional Qdrant, optional Ollama, and disabled-by-default OpenAI integration.

## What It Does Not Do

- No auto-apply.
- No credential scraping or authenticated job-board scraping.
- No CAPTCHA bypass or proxy rotation.
- No aggressive crawling.
- No required OpenAI API usage.

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

## Source Defaults

All requested companies and job-board references are present in `config/sources.yaml`. The MVP enables five high-signal company sources by default:

- Anthropic
- n8n
- Grafana Labs
- LangChain
- Qdrant

More sources can be toggled from the UI or by editing YAML. Many career pages need source-specific hardening over time; the MVP intentionally marks that honestly instead of pretending every site has a perfect adapter.

## Add A Company Source

Add an entry to `config/sources.yaml`:

```yaml
- company_name: ExampleCo
  career_url: https://example.com/careers
  source_type: company
  adapter_type: static_html
  remote_policy_notes: Remote-friendly by role.
  culture_notes: Search and AI infrastructure.
  priority: high
  include_keywords: [RAG, search, solutions, customer]
  exclude_keywords: [US only, onsite only]
  target_regions: [Europe, Germany, Remote]
  enabled: true
```

Use `static_html` for simple pages and `generic_playwright` for JavaScript-rendered pages. ATS adapter placeholders exist for Greenhouse, Lever, Ashby, Workable, and SmartRecruiters, with TODOs for company-specific hardening.

## Run A Scrape

From the UI:

- Dashboard: run all enabled sources.
- Sources: run one source.

From the API:

```bash
curl -X POST http://localhost:8000/api/scrape/run
curl -X POST http://localhost:8000/api/scrape/run/1
```

The worker also schedules a daily scrape at `DAILY_SCRAPE_TIME`, default `07:00 Europe/Berlin`.

## Tune Scoring

Edit `config/profile.yaml`:

- `target_role_families`
- `positive_keywords`
- `negative_keywords`
- `target_regions`
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
- Do not use proxies by default.
- Keep crawling polite and low-volume.
- Do not auto-apply to jobs.

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
