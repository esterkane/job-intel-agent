from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.config.loader import load_profile, load_search_profile, sync_sources
from app.db.session import get_session
from app.models import Job, ManualJobCapture, ScrapeRun, Source
from app.schemas.job import JobRead, JobUpdate, ManualCaptureCreate, ScrapeRunRead, SourceRead, SourceUpdate
from app.scoring.matcher import JobScorer
from app.scrapers.base import NormalizedJob
from app.services.ingestion import content_hash, run_source_scrape

router = APIRouter()

PRESERVED_JOB_STATUSES = {"saved", "applied"}
PLATFORM_SOURCE_TYPES = {
    "api_json",
    "public_static",
    "public_playwright",
    "rss_or_feed",
    "jobspy_optional",
    "manual_browser_only",
    "disabled_due_to_terms",
}


def delete_existing_imported_jobs(db: Session, source: Source | None = None) -> int:
    query = db.query(Job).filter(Job.status.notin_(PRESERVED_JOB_STATUSES))
    if source is not None:
        query = query.filter(Job.source_name == source.company_name)
    deleted = query.delete(synchronize_session=False)
    db.commit()
    return deleted


@router.get("/jobs", response_model=list[JobRead])
def list_jobs(
    min_score: float | None = None,
    company: str | None = None,
    status: str | None = None,
    new_only: bool = False,
    source: str | None = None,
    db: Session = Depends(get_session),
):
    query = db.query(Job)
    if min_score is not None:
        query = query.filter(Job.final_score >= min_score)
    if company:
        query = query.filter(Job.company == company)
    if status:
        query = query.filter(Job.status == status)
    if new_only:
        query = query.filter(Job.status == "new")
    if source:
        query = query.filter(Job.source_name == source)
    return query.order_by(desc(Job.final_score), desc(Job.first_seen_at)).limit(500).all()


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_session)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/jobs/{job_id}", response_model=JobRead)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_session)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.get("/sources", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_session)):
    sync_sources(db)
    return (
        db.query(Source)
        .filter(Source.source_type.in_(PLATFORM_SOURCE_TYPES))
        .order_by(desc(Source.enabled), Source.company_name)
        .all()
    )


@router.patch("/sources/{source_id}", response_model=SourceRead)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_session)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


async def _scrape_one(source_id: int) -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if source and source.enabled:
            await run_source_scrape(db, source)
    finally:
        db.close()


@router.post("/scrape/run")
def run_scrape(background_tasks: BackgroundTasks, fresh: bool = False, db: Session = Depends(get_session)):
    sync_sources(db)
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()
    deleted = 0
    if fresh:
        source_names = [source.company_name for source in sources]
        if source_names:
            deleted = (
                db.query(Job)
                .filter(Job.status.notin_(PRESERVED_JOB_STATUSES), Job.source_name.in_(source_names))
                .delete(synchronize_session=False)
            )
            db.commit()
    for source in sources:
        background_tasks.add_task(_scrape_one, source.id)
    return {"queued": len(sources), "fresh": fresh, "deleted": deleted}


@router.post("/scrape/run/{source_id}", response_model=ScrapeRunRead)
async def run_source(source_id: int, fresh: bool = False, db: Session = Depends(get_session)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if fresh:
        delete_existing_imported_jobs(db, source)
    return await run_source_scrape(db, source)


@router.get("/scrape/runs", response_model=list[ScrapeRunRead])
def list_runs(db: Session = Depends(get_session)):
    return db.query(ScrapeRun).order_by(desc(ScrapeRun.started_at)).limit(100).all()


@router.post("/manual-capture", response_model=JobRead)
def manual_capture(payload: ManualCaptureCreate, db: Session = Depends(get_session)):
    normalized = NormalizedJob(
        source_name="Manual Capture",
        source_type="manual_browser_only",
        company=payload.company,
        title=payload.title,
        location=payload.location,
        remote_type="remote" if "remote" in f"{payload.location or ''} {payload.description}".lower() else None,
        region="Germany/EU" if any(term in f"{payload.location or ''} {payload.description}".lower() for term in ["germany", "europe", "eu", "emea", "cet", "cest"]) else None,
        job_url=payload.url or f"manual://{payload.company}/{payload.title}",
        description=payload.description,
        raw_source={"adapter": "manual_capture"},
    )
    hash_value = content_hash(normalized)
    existing = (
        db.query(Job)
        .filter(Job.company == normalized.company, Job.title == normalized.title, Job.location == normalized.location, Job.job_url == normalized.job_url)
        .one_or_none()
    )
    scored = JobScorer(load_search_profile()).score(normalized.__dict__, company_priority="medium")
    values = {
        **normalized.__dict__,
        "content_hash": hash_value,
        "last_seen_at": datetime.now(UTC),
        "final_score": scored.final_score,
        "score_breakdown": scored.score_breakdown,
        "role_family": scored.role_family,
        "why_this_matches": scored.why_this_matches,
        "concerns": scored.concerns,
        "suggested_application_angle": scored.suggested_application_angle,
        "suggested_cv_emphasis": scored.suggested_cv_emphasis,
        "notes": payload.notes,
    }
    if existing:
        for key, value in values.items():
            if key not in {"status", "first_seen_at"}:
                setattr(existing, key, value)
        job = existing
    else:
        job = Job(**values)
        db.add(job)
        db.flush()
    db.add(ManualJobCapture(
        job_id=job.id,
        url=payload.url,
        title=payload.title,
        company=payload.company,
        description=payload.description,
        raw_payload_json=payload.model_dump(),
    ))
    db.commit()
    db.refresh(job)
    return job


@router.get("/stats")
def stats(db: Session = Depends(get_session)):
    total = db.query(func.count(Job.id)).scalar() or 0
    high = db.query(func.count(Job.id)).filter(Job.final_score >= 75, Job.status == "new").scalar() or 0
    saved = db.query(func.count(Job.id)).filter(Job.status == "saved").scalar() or 0
    applied = db.query(func.count(Job.id)).filter(Job.status == "applied").scalar() or 0
    errors = db.query(func.count(Source.id)).filter(Source.last_status == "error").scalar() or 0
    latest_run = db.query(ScrapeRun).order_by(desc(ScrapeRun.started_at)).first()
    return {
        "jobs_found_today": total,
        "new_high_fit_jobs": high,
        "saved_jobs": saved,
        "applied_jobs": applied,
        "sources_with_errors": errors,
        "latest_run_status": latest_run.status if latest_run else "never",
    }


@router.get("/profile")
def get_profile():
    return load_profile()


@router.get("/search-profile")
def get_search_profile():
    return load_search_profile()


@router.put("/search-profile")
def put_search_profile():
    raise HTTPException(status_code=501, detail="Search profile editing is a frontend placeholder in this MVP. Edit config/search_profile.yaml.")


@router.put("/profile")
def put_profile():
    raise HTTPException(status_code=501, detail="Profile editing is a frontend placeholder in this MVP. Edit config/search_profile.yaml.")
