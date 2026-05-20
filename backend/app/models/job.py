from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class JobStatus(str, Enum):
    new = "new"
    seen = "seen"
    saved = "saved"
    ignored = "ignored"
    applied = "applied"
    expired = "expired"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    career_url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(80), default="company")
    adapter_type: Mapped[str] = mapped_column(String(80), default="static_html")
    remote_policy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    culture_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    include_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    exclude_keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    target_regions: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_successful_scrape: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    scrape_runs: Mapped[list["ScrapeRun"]] = relationship(back_populates="source")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="running")
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[Source | None] = relationship(back_populates="scrape_runs")
    jobs: Mapped[list["Job"]] = relationship(back_populates="scrape_run")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("company", "title", "location", "job_url", name="uq_job_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(80), default="company")
    company: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    job_url: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    date_posted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(40), default=JobStatus.new.value)
    raw_source: Mapped[dict] = mapped_column(JSON, default=dict)
    scrape_run_id: Mapped[int | None] = mapped_column(ForeignKey("scrape_runs.id"), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    final_score: Mapped[float] = mapped_column(Float, default=0)
    role_family: Mapped[str | None] = mapped_column(String(255), nullable=True)
    why_this_matches: Mapped[str | None] = mapped_column(Text, nullable=True)
    concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_application_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_cv_emphasis: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    scrape_run: Mapped[ScrapeRun | None] = relationship(back_populates="jobs")


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    phrase: Mapped[str] = mapped_column(String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ManualJobCapture(Base):
    __tablename__ = "manual_job_captures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(255), default="Manual")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


JobPlatformSource = Source
JobPosting = Job
JobScore = Job
