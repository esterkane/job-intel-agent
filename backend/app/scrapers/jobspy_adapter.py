from app.scrapers.base import NormalizedJob, ScraperAdapter


class JobSpyAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        try:
            from jobspy import scrape_jobs
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("JobSpy is optional and is not installed or importable") from exc

        site_name = (source.company_name or "").lower().replace(" ", "")
        jobs_df = scrape_jobs(
            site_name=[site_name] if site_name in {"indeed", "linkedin", "zip_recruiter", "glassdoor", "google"} else ["google"],
            search_term="RAG OR AI Solutions Engineer OR Search Engineer remote Europe",
            location="Germany",
            results_wanted=25,
            hours_old=72,
        )
        jobs: list[NormalizedJob] = []
        for row in jobs_df.to_dict("records"):
            jobs.append(
                NormalizedJob(
                    source_name=source.company_name,
                    source_type=source.source_type,
                    company=row.get("company") or source.company_name,
                    title=row.get("title") or "Untitled role",
                    location=row.get("location"),
                    remote_type="remote" if "remote" in str(row.get("location", "")).lower() else None,
                    region="Europe" if "germany" in str(row.get("location", "")).lower() else None,
                    job_url=row.get("job_url") or source.career_url,
                    description=row.get("description"),
                    raw_source={"adapter": "jobspy", "row": row},
                )
            )
        return jobs
