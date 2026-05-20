from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config.loader import load_profile
from app.models import Job, ScrapeRun, Source
from app.scoring.matcher import JobScorer
from app.services.semantic import semantic_match, upsert_qdrant
from app.scrapers.ats_adapters import AshbyAdapter, GreenhouseAdapter, LeverAdapter, SmartRecruitersAdapter, WorkableAdapter
from app.scrapers.base import NormalizedJob, ScraperAdapter
from app.scrapers.filters import is_region_compatible
from app.scrapers.generic_playwright_adapter import GenericPlaywrightAdapter
from app.scrapers.jobspy_adapter import JobSpyAdapter
from app.scrapers.platform_adapters import (
    ArbeitnowAdapter,
    ManualBrowserSource,
    PublicPlaywrightAdapter,
    PublicStaticAdapter,
    WorkingNomadsAdapter,
)
from app.scrapers.static_html_adapter import StaticHtmlAdapter


def content_hash(job: NormalizedJob) -> str:
    value = "|".join([job.company, job.title, job.location or "", job.job_url, job.description or ""])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def adapter_for(source: Source) -> ScraperAdapter:
    if source.source_type == "api_json" and source.company_name.lower() == "arbeitnow":
        return ArbeitnowAdapter()
    if source.source_type == "api_json" and source.company_name.lower() == "working nomads":
        return WorkingNomadsAdapter()
    if source.source_type == "public_static":
        return PublicStaticAdapter()
    if source.source_type == "public_playwright":
        return PublicPlaywrightAdapter()
    if source.source_type in {"manual_browser_only", "disabled_due_to_terms"}:
        return ManualBrowserSource()
    if source.source_type == "jobspy_optional":
        return JobSpyAdapter()
    adapters: dict[str, ScraperAdapter] = {
        "static_html": StaticHtmlAdapter(),
        "generic_playwright": GenericPlaywrightAdapter(),
        "greenhouse": GreenhouseAdapter(),
        "lever": LeverAdapter(),
        "ashby": AshbyAdapter(),
        "workable": WorkableAdapter(),
        "smartrecruiters": SmartRecruitersAdapter(),
        "jobspy": JobSpyAdapter(),
    }
    return adapters.get(source.adapter_type, StaticHtmlAdapter())


def ingestion_method_for(source: Source) -> str:
    if source.source_type == "api_json":
        return "api"
    if source.source_type in {"public_static", "public_playwright"}:
        return "public_scrape"
    if source.source_type == "browser_allowed":
        return "browser_assist"
    return "public_scrape"


def upsert_jobs(db: Session, source: Source, run: ScrapeRun, jobs: list[NormalizedJob]) -> tuple[int, int]:
    scorer = JobScorer(load_profile())
    new_count = 0
    updated_count = 0
    now = datetime.now(UTC)
    for item in jobs:
        if not is_region_compatible(f"{item.title} {item.location or ''}"):
            continue
        hash_value = content_hash(item)
        existing = (
            db.query(Job)
            .filter(
                Job.company == item.company,
                Job.title == item.title,
                Job.location == item.location,
                Job.job_url == item.job_url,
            )
            .one_or_none()
        )
        scored = scorer.score(item.__dict__, company_priority=source.priority)
        embedding, semantic_score = semantic_match(f"{item.title}\n{item.description or ''}")
        final_score = scored.final_score
        breakdown = dict(scored.score_breakdown)
        if semantic_score is not None:
            breakdown["semantic_matching_score"] = semantic_score
            final_score = round((scored.final_score * 0.85) + (semantic_score * 0.15), 1)
        values = {
            **item.__dict__,
            "scrape_run_id": run.id,
            "content_hash": hash_value,
            "ingestion_method": ingestion_method_for(source),
            "last_seen_at": now,
            "final_score": final_score,
            "score_breakdown": breakdown,
            "role_family": scored.role_family,
            "why_this_matches": scored.why_this_matches,
            "concerns": scored.concerns,
            "suggested_application_angle": scored.suggested_application_angle,
            "suggested_cv_emphasis": scored.suggested_cv_emphasis,
            "embedding": embedding,
        }
        if existing:
            for key, value in values.items():
                if key not in {"status", "first_seen_at"}:
                    setattr(existing, key, value)
            db.flush()
            upsert_qdrant(existing.id, embedding, {"company": item.company, "title": item.title, "url": item.job_url})
            updated_count += 1
        else:
            job = Job(**values)
            db.add(job)
            db.flush()
            upsert_qdrant(job.id, embedding, {"company": item.company, "title": item.title, "url": item.job_url})
            new_count += 1
    db.commit()
    return new_count, updated_count


async def run_source_scrape(db: Session, source: Source) -> ScrapeRun:
    run = ScrapeRun(source_id=source.id)
    db.add(run)
    db.commit()
    db.refresh(run)
    try:
        jobs = await adapter_for(source).scrape(source)
        new_count, updated_count = upsert_jobs(db, source, run, jobs)
        run.status = "success"
        run.jobs_found = len(jobs)
        run.jobs_new = new_count
        run.jobs_updated = updated_count
        run.finished_at = datetime.now(UTC)
        source.last_status = "success"
        source.last_error = None
        source.last_successful_scrape = run.finished_at
    except Exception as exc:
        run.status = "error"
        run.error_message = str(exc)
        run.finished_at = datetime.now(UTC)
        source.last_status = "error"
        source.last_error = str(exc)
    db.commit()
    db.refresh(run)
    return run
