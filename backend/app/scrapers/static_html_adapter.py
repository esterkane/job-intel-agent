from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import NormalizedJob, ScraperAdapter
from app.scrapers.filters import clean_text, is_probable_job_link, is_region_compatible


class StaticHtmlAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(source.career_url, headers={"User-Agent": "job-intel-agent/0.1 polite local research"})
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        jobs: list[NormalizedJob] = []
        seen: set[str] = set()
        for link in soup.find_all("a", href=True):
            text = clean_text(link.get_text(" ", strip=True))
            context = clean_text(link.find_parent(["li", "article", "section", "div"]).get_text(" ", strip=True) if link.find_parent(["li", "article", "section", "div"]) else text)
            url = urljoin(source.career_url, link["href"])
            if not is_probable_job_link(text, url, context):
                continue
            if not is_region_compatible(f"{text} {context}"):
                continue
            key = f"{text}|{url}"
            if key in seen:
                continue
            seen.add(key)
            jobs.append(
                NormalizedJob(
                    source_name=source.company_name,
                    source_type=source.source_type,
                    company=source.company_name,
                    title=text[:500],
                    location=self._guess_location(context),
                    remote_type="remote" if "remote" in context.lower() else None,
                    region=self._guess_region(context),
                    job_url=url,
                    description=context[:8000],
                    raw_source={"adapter": "static_html", "snapshot": soup.get_text(" ", strip=True)[:12000]},
                )
            )
        return jobs[:80]

    def _guess_location(self, text: str) -> str | None:
        lowered = text.lower()
        for token in ["remote worldwide", "work from anywhere", "remote", "emea", "europe", "germany", "berlin", "london", "sweden", "uk", "france", "italy", "spain"]:
            if token in lowered:
                return token.title()
        return None

    def _guess_region(self, text: str) -> str | None:
        lowered = text.lower()
        if "work from anywhere" in lowered or "remote worldwide" in lowered or "anywhere" in lowered:
            return "Worldwide"
        if any(term in lowered for term in ["germany", "europe", "emea", "sweden", "uk", "united kingdom", "france", "italy", "spain"]):
            return "Europe"
        if "remote" in lowered:
            return "Remote"
        return None