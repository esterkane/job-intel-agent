from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.settings import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_kwargs = {"poolclass": StaticPool} if settings.database_url == "sqlite:///:memory:" else {"pool_pre_ping": True}
engine = create_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from app.models import job  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_compat_columns()


def _ensure_compat_columns() -> None:
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return
    job_columns = {column["name"] for column in inspector.get_columns("jobs")}
    if "ingestion_method" not in job_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN ingestion_method VARCHAR(40) DEFAULT 'public_scrape'"))


def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
