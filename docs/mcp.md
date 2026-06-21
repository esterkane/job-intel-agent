# Agent Access (MCP)

`job-intel-agent` ships a **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server that exposes the job-intelligence core as agent tools. Any MCP client —
Claude Code, Cursor, or a LangGraph agent — can query scored jobs and the
configured sources without going through the HTTP API or a browser.

The server is a **thin adapter**: every tool reuses an existing query helper,
service, or schema in `backend/app/`. There is no business logic in the MCP
layer, and it is **strictly read-only** — scrape-run / ingest / manual-capture
and any other mutation are deliberately **not** exposed.

## Tools

All three tools mirror the shapes of the corresponding HTTP endpoints.

### `search_jobs(query?, filters?)`

List/filter scored job postings, ordered best-fit first (highest deterministic
`final_score`, then most recently first seen). Mirrors `GET /api/jobs`.

- `query` (str, optional): case-insensitive substring matched against the job
  **title** and **company**. Omit to list everything (subject to filters).
- `filters` (object, optional), all keys optional, mirroring `GET /api/jobs`:
  - `min_score` (number) — only jobs with `final_score >=` this value
  - `company` (str) — exact company name
  - `status` (str) — `new | seen | saved | ignored | applied | expired`
  - `new_only` (bool) — shortcut for `status == "new"`
  - `source` (str) — exact `source_name`
  - `limit` (int, 1..500, default 500) — max jobs to return

Returns `{query, count, jobs: [Job]}`.

### `get_job(job_id)`

Fetch one scored job by its integer id. Mirrors `GET /api/jobs/{id}`.

- `job_id` (int, required) — the `id` from a `search_jobs` result.

Returns `{job: Job}`. An unknown id is a **business** error (see below).

### `list_sources()`

List the configured job-platform sources (enabled-first, then by name), each
with type, adapter, enablement, priority, regions, and last scrape status.
Mirrors `GET /api/sources`. Internal-only origins such as `manual_capture` are
excluded — this is the platform catalog, not a job list.

Returns `{count, sources: [Source]}`.

### The `Job` shape

`search_jobs` and `get_job` return jobs in the API's `JobRead` shape **plus**
`content_hash`, so every result carries the full provenance set:

```
id, source_name, source_type, company, title, location, remote_type, region,
job_url, description, department, employment_type, first_seen_at, last_seen_at,
status, ingestion_method, final_score, role_family, score_breakdown,
why_this_matches, concerns, suggested_application_angle, suggested_cv_emphasis,
notes, content_hash
```

Provenance fields preserved on every job: `source_name`, `source_type`,
`ingestion_method`, `content_hash`, `first_seen_at`, `last_seen_at`. The
`final_score` / `score_breakdown` / `why_this_matches` come straight from the
persisted deterministic `JobScorer` output — the MCP layer never re-scores, so
output stays deterministic.

## Error contract

Tools never raise or leak a stack trace. Expected failures return a structured
payload instead of a result:

```json
{
  "isError": true,
  "errorCategory": "validation | transient | permission | business",
  "isRetryable": true,
  "message": "<safe, human-readable summary>",
  "details": { }
}
```

| Category     | When                                                        | Retryable |
|--------------|-------------------------------------------------------------|-----------|
| `validation` | Bad input (unknown filter key, `limit` out of range, non-string `query`, non-integer `job_id`) | no |
| `business`   | Valid request that can't be satisfied (unknown `job_id`)    | no        |
| `transient`  | Database / outbound source momentarily unreachable (SQLAlchemy / httpx) | yes |
| `permission` | Reserved; not currently emitted by any read-only tool       | no        |

An empty `jobs`/`sources` list with no `isError` simply means nothing matched.

## Running the server

Working directory is `backend/` (the package import root is `app`, matching the
HTTP app and the test suite).

```bash
cd backend
pip install -e ".[test]"        # or just the runtime deps; `mcp` is a runtime dep
python -m app.mcp.server         # stdio transport (default)
```

Transport is selected by `MCP_TRANSPORT`:

- `stdio` (default) — for local dev and Claude Code / Cursor.
- `http` — streamable-HTTP for a networked client (`MCP_TRANSPORT=http`).

The server calls `init_db()` on startup (same as the FastAPI app) and reads the
same `DATABASE_URL` from `backend/.env`, so it talks to the identical database
the API uses (Postgres in prod, SQLite in tests).

## Client registration (Claude Code / Cursor)

Register the stdio server in your MCP client config. Example (`mcp.json`):

```json
{
  "mcpServers": {
    "job-intel-agent": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "/absolute/path/to/job-intel-agent/backend",
      "env": { "MCP_TRANSPORT": "stdio" }
    }
  }
}
```

On Windows, point `command` at the project venv interpreter, e.g.
`/absolute/path/to/job-intel-agent/.venv/Scripts/python.exe`.

## Examples

```jsonc
// High-scoring new AI-search jobs
search_jobs("search", { "min_score": 75, "new_only": true })

// Everything from one source
search_jobs(null, { "source": "Arbeitnow" })

// Drill into one posting
get_job(42)

// Which platforms are configured / enabled?
list_sources()
```

## Design notes / invariants

- **Thin adapters only.** Tool logic lives in `backend/app/mcp/tools.py` as pure
  importable async functions taking an explicit `session`; they reuse the same
  SQLAlchemy filter shape as `GET /api/jobs`, the `JobRead`/`SourceRead` schemas,
  and the shared `list_platform_sources` service behind `GET /api/sources`.
- **Read-only.** No mutating tool is registered. The only write in any call path
  is the idempotent config upsert `sync_sources` performs inside `list_sources`
  (identical to `GET /api/sources`).
- **Deterministic.** Tools surface the persisted deterministic score; they never
  re-run the scorer.
- **Structured errors, no leaks.** The `guard` decorator converts every failure
  to the structured payload above; SQLAlchemy/httpx errors map to retryable
  `transient`.
