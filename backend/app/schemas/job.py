from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    career_url: str
    source_type: str
    adapter_type: str
    remote_policy_notes: str | None
    culture_notes: str | None
    priority: str
    include_keywords: list[str]
    exclude_keywords: list[str]
    target_regions: list[str]
    enabled: bool
    last_status: str | None
    last_error: str | None
    last_successful_scrape: datetime | None


class SourceUpdate(BaseModel):
    enabled: bool | None = None
    priority: str | None = None
    include_keywords: list[str] | None = None
    exclude_keywords: list[str] | None = None
    target_regions: list[str] | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    source_type: str
    company: str
    title: str
    location: str | None
    remote_type: str | None
    region: str | None
    job_url: str
    description: str | None
    department: str | None
    employment_type: str | None
    first_seen_at: datetime
    last_seen_at: datetime
    status: str
    final_score: float
    role_family: str | None
    score_breakdown: dict[str, Any]
    why_this_matches: str | None
    concerns: str | None
    suggested_application_angle: str | None
    suggested_cv_emphasis: str | None
    notes: str | None


class JobUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


class ManualCaptureCreate(BaseModel):
    url: str | None = None
    title: str
    company: str = "Manual"
    location: str | None = None
    description: str
    notes: str | None = None


class ScrapeRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int | None
    started_at: datetime
    finished_at: datetime | None
    status: str
    jobs_found: int
    jobs_new: int
    jobs_updated: int
    error_message: str | None
