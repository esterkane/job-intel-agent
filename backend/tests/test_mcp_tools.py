"""Unit tests for the read-only MCP tool impls.

These call the pure async handlers in ``app.mcp.tools`` directly against the
in-memory SQLite session configured by ``conftest`` (DATABASE_URL =
sqlite:///:memory:), with no FastMCP or HTTP coupling. ``asyncio.run`` drives the
coroutines so the suite needs no event-loop fixture.
"""

import asyncio

from app.db.session import SessionLocal, init_db
from app.mcp.tools import get_job_impl, list_sources_impl, search_jobs_impl
from app.models import Job

# Provenance fields every tool result must carry for a job (the project invariant).
PROVENANCE_FIELDS = {
    "source_name",
    "source_type",
    "ingestion_method",
    "content_hash",
    "first_seen_at",
    "last_seen_at",
}


def _seed_job(**overrides) -> int:
    init_db()
    db = SessionLocal()
    try:
        values = {
            "source_name": "Test Source",
            "source_type": "api_json",
            "company": "Grafana Labs",
            "title": "AI Search Engineer",
            "location": "Remote Germany",
            "remote_type": "remote",
            "region": "Germany/EU",
            "job_url": "https://example.com/job-1",
            "description": "Build RAG retrieval over Elasticsearch.",
            "content_hash": "hash-1",
            "ingestion_method": "public_scrape",
            "final_score": 88.0,
            "score_breakdown": {"search_rag_score": 95},
        }
        values.update(overrides)
        job = Job(**values)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def _clear_jobs() -> None:
    init_db()
    db = SessionLocal()
    try:
        db.query(Job).delete()
        db.commit()
    finally:
        db.close()


# --- search_jobs ------------------------------------------------------------


def test_search_jobs_success_shape_and_provenance():
    _clear_jobs()
    _seed_job()
    db = SessionLocal()
    try:
        result = asyncio.run(search_jobs_impl("search", filters=None, session=db))
    finally:
        db.close()

    assert "isError" not in result
    assert result["query"] == "search"
    assert result["count"] == 1
    job = result["jobs"][0]
    assert job["company"] == "Grafana Labs"
    assert job["final_score"] == 88.0
    # Full provenance set is present and populated.
    assert PROVENANCE_FIELDS.issubset(job.keys())
    assert job["content_hash"] == "hash-1"


def test_search_jobs_filters_by_min_score_and_query():
    _clear_jobs()
    _seed_job(job_url="https://example.com/a", content_hash="a", title="AI Search Engineer", final_score=90.0)
    _seed_job(job_url="https://example.com/b", content_hash="b", title="Frontline Support", final_score=20.0)
    db = SessionLocal()
    try:
        # query narrows to title/company; min_score filters the low one out.
        result = asyncio.run(
            search_jobs_impl("search", filters={"min_score": 50}, session=db)
        )
    finally:
        db.close()
    assert result["count"] == 1
    assert result["jobs"][0]["title"] == "AI Search Engineer"


def test_search_jobs_rejects_unknown_filter_key():
    db = SessionLocal()
    try:
        result = asyncio.run(
            search_jobs_impl(None, filters={"bogus": True}, session=db)
        )
    finally:
        db.close()
    assert result["isError"] is True
    assert result["errorCategory"] == "validation"
    assert result["isRetryable"] is False


def test_search_jobs_rejects_out_of_range_limit():
    db = SessionLocal()
    try:
        result = asyncio.run(
            search_jobs_impl(None, filters={"limit": 9999}, session=db)
        )
    finally:
        db.close()
    assert result["isError"] is True
    assert result["errorCategory"] == "validation"


# --- get_job ----------------------------------------------------------------


def test_get_job_success():
    _clear_jobs()
    job_id = _seed_job()
    db = SessionLocal()
    try:
        result = asyncio.run(get_job_impl(job_id, session=db))
    finally:
        db.close()
    assert "isError" not in result
    assert result["job"]["id"] == job_id
    assert PROVENANCE_FIELDS.issubset(result["job"].keys())


def test_get_job_unknown_id_is_business_error():
    _clear_jobs()
    db = SessionLocal()
    try:
        result = asyncio.run(get_job_impl(999999, session=db))
    finally:
        db.close()
    assert result["isError"] is True
    assert result["errorCategory"] == "business"
    assert result["isRetryable"] is False
    assert result["details"]["job_id"] == 999999


def test_get_job_non_integer_is_validation_error():
    db = SessionLocal()
    try:
        result = asyncio.run(get_job_impl("not-an-int", session=db))  # type: ignore[arg-type]
    finally:
        db.close()
    assert result["isError"] is True
    assert result["errorCategory"] == "validation"


# --- list_sources -----------------------------------------------------------


def test_list_sources_success_shape():
    init_db()
    db = SessionLocal()
    try:
        result = asyncio.run(list_sources_impl(session=db))
    finally:
        db.close()
    assert "isError" not in result
    assert result["count"] == len(result["sources"])
    if result["sources"]:
        source = result["sources"][0]
        assert "company_name" in source
        assert "source_type" in source
        assert "enabled" in source


# --- transient backend error mapping ----------------------------------------


class _BrokenSession:
    """A fake session whose every query path raises an SQLAlchemy error, to
    prove `guard` maps DB failures to a retryable transient error rather than
    leaking the exception."""

    def query(self, *args, **kwargs):
        from sqlalchemy.exc import OperationalError

        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    def get(self, *args, **kwargs):
        from sqlalchemy.exc import OperationalError

        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_search_jobs_transient_backend_error():
    result = asyncio.run(
        search_jobs_impl(None, filters=None, session=_BrokenSession())  # type: ignore[arg-type]
    )
    assert result["isError"] is True
    assert result["errorCategory"] == "transient"
    assert result["isRetryable"] is True


def test_get_job_transient_backend_error():
    result = asyncio.run(
        get_job_impl(1, session=_BrokenSession())  # type: ignore[arg-type]
    )
    assert result["isError"] is True
    assert result["errorCategory"] == "transient"
    assert result["isRetryable"] is True
