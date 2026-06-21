"""MCP tool handlers wrapping the job-intelligence core.

These are plain, importable async functions — no FastMCP or HTTP coupling — so
they can be unit-tested directly against the in-memory SQLite session used by
the backend test suite (or a fake). ``app/mcp/server.py`` registers thin FastMCP
wrappers that open a session from the backend's ``SessionLocal`` and call these.

Every handler is wrapped by :func:`app.mcp.errors.guard`, so it either returns a
structured success payload or a structured error payload — never a raised
exception or a stack trace.

The handlers are deliberately THIN: they reuse the SQLAlchemy query/filter
shape of ``GET /api/jobs`` and ``GET /api/jobs/{id}``, the shared
``list_platform_sources`` service behind ``GET /api/sources``, and the existing
``JobRead`` / ``SourceRead`` Pydantic schemas for serialisation. They add no
business logic and never mutate data. The deterministic ``JobScorer`` is not
re-run here — tools surface the persisted ``final_score`` / ``score_breakdown``
exactly as the HTTP API does, so output stays deterministic.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.mcp.errors import ToolBusinessError, ToolValidationError, guard
from app.models import Job
from app.schemas.job import JobRead, SourceRead
from app.services.sources import list_platform_sources

# Mirror the API's `.limit(500)` cap on /api/jobs; also the hard ceiling a
# caller may request via `limit`.
MAX_LIMIT = 500


class JobFilters(BaseModel):
    """Validated filter set for :func:`search_jobs_impl`.

    Mirrors the query parameters of ``GET /api/jobs`` one-for-one. Unknown keys
    are rejected so a caller learns about a typo instead of having it silently
    ignored.
    """

    model_config = ConfigDict(extra="forbid")

    min_score: float | None = None
    company: str | None = None
    status: str | None = None
    new_only: bool = False
    source: str | None = None
    limit: int = Field(default=MAX_LIMIT, ge=1, le=MAX_LIMIT)


def _job_payload(job: Job) -> dict[str, Any]:
    """Serialise a Job to the API's ``JobRead`` shape plus explicit provenance.

    ``JobRead`` already carries ``source_name``, ``source_type``,
    ``ingestion_method``, ``first_seen_at`` and ``last_seen_at``; ``content_hash``
    is added here so every tool result carries the full provenance set an agent
    needs to trust and de-duplicate a posting.
    """
    payload = JobRead.model_validate(job).model_dump(mode="json")
    payload["content_hash"] = job.content_hash
    return payload


@guard("search_jobs")
async def search_jobs_impl(
    query: str | None = None,
    *,
    filters: dict[str, Any] | None = None,
    session: Session,
) -> dict[str, Any]:
    """Search/list scored jobs. Returns a structured payload. Read-only.

    ``query`` is an optional case-insensitive substring matched against the job
    title and company (the agent-facing equivalent of scanning the dashboard).
    ``filters`` mirrors ``GET /api/jobs`` (min_score, company, status, new_only,
    source, limit). Results are ordered best-score-first, matching the API.
    """
    if query is not None and not isinstance(query, str):
        raise ToolValidationError("`query` must be a string when provided.")
    normalized_query = query.strip() if isinstance(query, str) else None

    try:
        parsed = JobFilters.model_validate(filters or {})
    except ValidationError as exc:
        raise ToolValidationError(
            "Invalid `filters`.", details={"errors": exc.errors(include_url=False)}
        ) from exc

    db_query = session.query(Job)
    if parsed.min_score is not None:
        db_query = db_query.filter(Job.final_score >= parsed.min_score)
    if parsed.company:
        db_query = db_query.filter(Job.company == parsed.company)
    if parsed.status:
        db_query = db_query.filter(Job.status == parsed.status)
    if parsed.new_only:
        db_query = db_query.filter(Job.status == "new")
    if parsed.source:
        db_query = db_query.filter(Job.source_name == parsed.source)
    if normalized_query:
        like = f"%{normalized_query}%"
        db_query = db_query.filter(Job.title.ilike(like) | Job.company.ilike(like))

    jobs = (
        db_query.order_by(desc(Job.final_score), desc(Job.first_seen_at))
        .limit(parsed.limit)
        .all()
    )
    return {
        "query": normalized_query,
        "count": len(jobs),
        "jobs": [_job_payload(job) for job in jobs],
    }


@guard("get_job")
async def get_job_impl(job_id: int, *, session: Session) -> dict[str, Any]:
    """Fetch a single scored job by its integer id. Read-only.

    Mirrors ``GET /api/jobs/{id}``: an unknown id is a *business* error (a valid
    request that cannot be satisfied), not a transient failure.
    """
    if isinstance(job_id, bool) or not isinstance(job_id, int):
        raise ToolValidationError("`job_id` must be an integer.", details={"job_id": job_id})

    job = session.get(Job, job_id)
    if job is None:
        raise ToolBusinessError(
            f"No job exists with id {job_id}.", details={"job_id": job_id}
        )
    return {"job": _job_payload(job)}


@guard("list_sources")
async def list_sources_impl(*, session: Session) -> dict[str, Any]:
    """List the configured job-platform sources. Read-only.

    Reuses the same ``list_platform_sources`` service behind ``GET /api/sources``
    so the catalog and its enabled-first ordering match the HTTP API exactly.
    """
    sources = list_platform_sources(session)
    return {
        "count": len(sources),
        "sources": [SourceRead.model_validate(source).model_dump(mode="json") for source in sources],
    }
