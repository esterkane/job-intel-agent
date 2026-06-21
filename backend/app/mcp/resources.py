"""Resource wiring for the MCP layer.

The MCP server is a sibling front-end to the FastAPI app: both adapt the same
job-intelligence core to a transport. Rather than build its own engine, the MCP
layer reuses the backend's configured ``SessionLocal`` / ``engine`` and the same
``init_db`` table bootstrap the FastAPI app runs at startup, so it talks to the
identical database wired from ``Settings`` (Postgres in prod, SQLite in tests).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.db.session import SessionLocal, init_db


def ensure_schema() -> None:
    """Create tables if they do not yet exist (idempotent), matching the
    FastAPI app's startup. Safe to call once before serving."""
    init_db()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a backend DB session and always close it, mirroring the API's
    ``get_session`` dependency. The MCP tools are read-only, so no commit is
    issued here; the only writes in the call path are the idempotent config
    upsert performed by ``sync_sources`` inside ``list_sources``."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
