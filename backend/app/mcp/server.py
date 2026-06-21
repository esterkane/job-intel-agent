"""FastMCP server for job-intel-agent.

Exposes the job-intelligence core as three READ-ONLY MCP tools that any MCP
client (Claude Code, Cursor, a LangGraph agent) can call:

- ``search_jobs``  — list/filter scored jobs (the agent-facing dashboard query).
- ``get_job``      — fetch one scored job by id, with full provenance.
- ``list_sources`` — the catalog of configured job-platform sources.

The tool *logic* lives in :mod:`app.mcp.tools` as plain async functions; the
wrappers here open a DB session from the backend's ``SessionLocal`` and supply it.

This server is strictly read-only: scrape-run / ingest / manual-capture and any
other mutation are deliberately NOT registered as tools. As a defence in depth,
mutations would only ever be considered if ``MCP_ALLOW_MUTATIONS`` were set true
(it defaults to false and no mutating tool exists today).

Transport is selected by ``MCP_TRANSPORT``: ``stdio`` (default, for local dev and
Claude Code) or ``http`` (streamable-HTTP for a networked client).

Run it (working dir ``backend/``)::

    python -m app.mcp.server
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.mcp.resources import ensure_schema, session_scope
from app.mcp.tools import get_job_impl, list_sources_impl, search_jobs_impl

mcp = FastMCP("job-intel-agent")


@mcp.tool()
async def search_jobs(
    query: str | None = None,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Search and list scored job postings. READ-ONLY.

    WHAT IT DOES: Returns scored, deduplicated job postings from the local
    database, ordered best-fit first (highest deterministic `final_score`, then
    most recently first seen). This is the agent-facing equivalent of scanning
    the dashboard's job list. Each job carries its deterministic score and
    explanation plus full provenance (source_name, source_type, ingestion_method,
    content_hash, first_seen_at, last_seen_at).

    WHEN TO USE: To find or browse candidate roles by keyword and/or structured
    filters — e.g. "high-scoring new AI-search jobs", "everything from a given
    source", "saved jobs". Use this first, then `get_job` to drill into one.

    WHEN NOT TO USE: To fetch a known job by id, use `get_job`. To enumerate the
    configured platforms (not jobs), use `list_sources`. This tool never starts a
    scrape or ingests new data — it only reads what has already been collected.

    INPUTS:
      - query (str, optional): case-insensitive substring matched against the job
        title and company. Omit to list everything (subject to filters).
      - filters (object, optional), all optional, mirroring GET /api/jobs:
          - min_score (number): only jobs with final_score >= this value.
          - company (str): exact company name.
          - status (str): one of new | seen | saved | ignored | applied | expired.
          - new_only (bool): shortcut for status == "new".
          - source (str): exact source_name.
          - limit (int, 1..500, default 500): max jobs to return.

    OUTPUT: {query, count, jobs: [Job]}. Each Job: {id, source_name, source_type,
    company, title, location, remote_type, region, job_url, description,
    department, employment_type, first_seen_at, last_seen_at, status,
    ingestion_method, final_score, role_family, score_breakdown, why_this_matches,
    concerns, suggested_application_angle, suggested_cv_emphasis, notes,
    content_hash}. `jobs` is ordered best-first and may be empty.

    EDGE CASES & FAILURES: An empty `jobs` list with no error means nothing
    matched. On failure a structured error is returned instead:
    errorCategory="validation" (e.g. unknown filter key, limit out of range,
    non-string query) is not retryable; "transient" (database unreachable) is
    retryable. Stack traces are never returned.
    """
    with session_scope() as session:
        return await search_jobs_impl(query, filters=filters, session=session)


@mcp.tool()
async def get_job(job_id: int) -> dict[str, Any]:
    """Fetch a single scored job posting by its integer id. READ-ONLY.

    WHAT IT DOES: Returns one job with its deterministic score, score breakdown,
    match explanation, suggested application angle / CV emphasis, and full
    provenance (source_name, source_type, ingestion_method, content_hash,
    first_seen_at, last_seen_at). Mirrors GET /api/jobs/{id}.

    WHEN TO USE: After `search_jobs` surfaces an interesting `id`, to read the
    full detail of that posting.

    WHEN NOT TO USE: To search or browse, use `search_jobs`. To list platforms,
    use `list_sources`.

    INPUTS:
      - job_id (int, required): the integer id of the job (the `id` field from a
        `search_jobs` result).

    OUTPUT: {job: Job} with the same Job shape as `search_jobs`.

    EDGE CASES & FAILURES: An id that does not exist returns a structured
    errorCategory="business" error (a valid request that cannot be satisfied —
    not retryable). A non-integer id returns errorCategory="validation".
    "transient" (database unreachable) is retryable. Stack traces are never
    returned.
    """
    with session_scope() as session:
        return await get_job_impl(job_id, session=session)


@mcp.tool()
async def list_sources() -> dict[str, Any]:
    """List the configured job-platform sources. READ-ONLY.

    WHAT IT DOES: Returns the catalog of configured job platforms (from
    config/job_platforms.yaml / config/sources.yaml), enabled-first then by name,
    each with its type, adapter, enablement, priority, target regions, and last
    scrape status. Mirrors GET /api/sources. Internal-only origins such as
    manual_capture are excluded — this is the platform catalog, not a job list.

    WHEN TO USE: To discover which sources exist and which are enabled before
    interpreting `source` filters in `search_jobs`, or to report source health.

    WHEN NOT TO USE: To search jobs, use `search_jobs`. This tool returns source
    metadata only and never triggers a scrape.

    INPUTS: none.

    OUTPUT: {count, sources: [{id, company_name, career_url, source_type,
    adapter_type, remote_policy_notes, culture_notes, priority, include_keywords,
    exclude_keywords, target_regions, enabled, last_status, last_error,
    last_successful_scrape}]}.

    EDGE CASES & FAILURES: On failure a structured error is returned:
    "transient" (database unreachable, retryable). Stack traces are never
    returned.
    """
    with session_scope() as session:
        return await list_sources_impl(session=session)


def main() -> None:
    """Run the FastMCP server on the configured transport (stdio by default)."""
    ensure_schema()
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
