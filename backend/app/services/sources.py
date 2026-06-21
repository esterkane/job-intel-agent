"""Source listing shared by the HTTP route and the MCP tool.

The set of configured platform sources is derived from ``config/*.yaml`` and
synced into the ``sources`` table by :func:`app.config.loader.sync_sources`.
Both ``GET /api/sources`` and the ``list_sources`` MCP tool must return the same
rows, so the sync + filter + ordering logic lives here once and is imported by
each transport. This is read-only apart from the idempotent config sync that
``sync_sources`` performs.
"""

from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config.loader import sync_sources
from app.models import Source

# Source types that represent configured job *platforms* (everything declared in
# config/job_platforms.yaml or config/sources.yaml). Internal-only origins such
# as ``manual_capture`` are intentionally excluded from the platform catalog.
PLATFORM_SOURCE_TYPES = {
    "api_json",
    "public_static",
    "public_playwright",
    "rss_or_feed",
    "jobspy_optional",
    "manual_browser_only",
    "browser_allowed",
    "disabled_due_to_terms",
}


def list_platform_sources(db: Session) -> list[Source]:
    """Sync configured platforms into the DB, then return the platform catalog.

    Ordered enabled-first, then by company name — the same ordering the API
    serves. ``sync_sources`` is an idempotent upsert from config; it never
    scrapes or mutates job data.
    """
    sync_sources(db)
    return (
        db.query(Source)
        .filter(Source.source_type.in_(PLATFORM_SOURCE_TYPES))
        .order_by(desc(Source.enabled), Source.company_name)
        .all()
    )
