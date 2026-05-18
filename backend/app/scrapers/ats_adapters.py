import re
from urllib.parse import urljoin, urlparse

import httpx

from app.scrapers.base import NormalizedJob, ScraperAdapter
from app.scrapers.filters import is_region_compatible


class GreenhouseAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        token = self._board_token(source)
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(api_url, headers={"User-Agent": "job-intel-agent/0.1 polite local research"})
            response.raise_for_status()
        payload = response.json()
        jobs: list[NormalizedJob] = []
        for item in payload.get("jobs", []):
            title = item.get("title") or "Untitled role"
            offices = item.get("offices") or []
            departments = item.get("departments") or []
            location = item.get("location", {}).get("name") or "; ".join(
                office.get("name", "") for office in offices if office.get("name")
            )
            department = "; ".join(dept.get("name", "") for dept in departments if dept.get("name")) or None
            description = item.get("content") or title
            region_signal = f"{title} {location or ''} {department or ''}"
            if not is_region_compatible(region_signal):
                continue
            combined = f"{region_signal} {description or ''}"
            jobs.append(
                NormalizedJob(
                    source_name=source.company_name,
                    source_type=source.source_type,
                    company=source.company_name,
                    title=title[:500],
                    location=location,
                    remote_type="remote" if "remote" in combined.lower() else None,
                    region=self._guess_region(region_signal),
                    job_url=item.get("absolute_url") or f"https://job-boards.greenhouse.io/{token}/jobs/{item.get('id', '')}",
                    description=description,
                    department=department,
                    employment_type=None,
                    raw_source={"adapter": "greenhouse", "greenhouse_id": item.get("id"), "api_url": api_url},
                )
            )
        return jobs

    def _board_token(self, source) -> str:
        parsed = urlparse(source.career_url)
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if "greenhouse.io" in parsed.netloc and parts:
            return parts[0]
        return re.sub(r"[^a-z0-9]+", "", source.company_name.lower())

    def _guess_region(self, text: str) -> str | None:
        lowered = text.lower()
        if any(term in lowered for term in ["work from anywhere", "remote worldwide", "anywhere in the world", "global remote"]):
            return "Worldwide"
        if any(term in lowered for term in ["germany", "europe", "emea", "uk", "united kingdom", "london", "dublin", "ireland", "amsterdam", "sweden", "france", "italy", "spain", "netherlands", "cet", "cest"]):
            return "Europe"
        if "remote" in lowered:
            return "Remote"
        return None


class LeverAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        from app.scrapers.static_html_adapter import StaticHtmlAdapter

        return await StaticHtmlAdapter().scrape(source)


class AshbyAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        slug = self._board_slug(source)
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(api_url, headers={"User-Agent": "job-intel-agent/0.1 polite local research"})
            response.raise_for_status()
        payload = response.json()
        jobs: list[NormalizedJob] = []
        for item in payload.get("jobs", []):
            title = item.get("title") or "Untitled role"
            location = item.get("locationName") or item.get("location")
            department = item.get("departmentName") or item.get("department")
            employment_type = item.get("employmentType")
            description = item.get("descriptionPlain") or item.get("descriptionHtml") or title
            region_signal = f"{title} {location or ''} {department or ''} {employment_type or ''}"
            if not is_region_compatible(region_signal):
                continue
            combined = f"{region_signal} {description or ''}"
            jobs.append(
                NormalizedJob(
                    source_name=source.company_name,
                    source_type=source.source_type,
                    company=source.company_name,
                    title=title[:500],
                    location=location,
                    remote_type="remote" if "remote" in combined.lower() else None,
                    region=self._guess_region(region_signal),
                    job_url=item.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{item.get('id', '')}",
                    description=description,
                    department=department,
                    employment_type=employment_type,
                    raw_source={"adapter": "ashby", "ashby_id": item.get("id"), "api_url": api_url},
                )
            )
        return jobs

    def _board_slug(self, source) -> str:
        parsed = urlparse(source.career_url)
        if "ashbyhq.com" in parsed.netloc and parsed.path.strip("/"):
            return parsed.path.strip("/").split("/")[0]
        return re.sub(r"[^a-z0-9]+", "", source.company_name.lower())

    def _guess_region(self, text: str) -> str | None:
        lowered = text.lower()
        if any(term in lowered for term in ["work from anywhere", "remote worldwide", "anywhere in the world", "global remote"]):
            return "Worldwide"
        if any(term in lowered for term in ["germany", "europe", "emea", "uk", "united kingdom", "london", "amsterdam", "sweden", "france", "italy", "spain", "netherlands", "cet", "cest"]):
            return "Europe"
        if "remote" in lowered:
            return "Remote"
        return None


class WorkableAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        from app.scrapers.static_html_adapter import StaticHtmlAdapter

        return await StaticHtmlAdapter().scrape(source)


class SmartRecruitersAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(source.career_url)
            response.raise_for_status()
        return [
            NormalizedJob(
                source_name=source.company_name,
                source_type=source.source_type,
                company=source.company_name,
                title="SmartRecruiters source discovered",
                location=None,
                remote_type=None,
                region=None,
                job_url=urljoin(source.career_url, ""),
                description="TODO: add company-specific SmartRecruiters API mapping.",
                raw_source={"adapter": "smartrecruiters", "snapshot": response.text[:12000]},
            )
        ] if False else []
