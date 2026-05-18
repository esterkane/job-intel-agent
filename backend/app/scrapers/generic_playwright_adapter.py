import asyncio
from urllib.parse import urljoin

from app.core.settings import get_settings
from app.scrapers.base import NormalizedJob, ScraperAdapter
from app.scrapers.filters import clean_text, is_probable_job_link, is_region_compatible


class GenericPlaywrightAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        from playwright.async_api import async_playwright

        settings = get_settings()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(user_agent="job-intel-agent/0.1 polite local research")
            await page.goto(source.career_url, wait_until="networkidle", timeout=settings.scrape_timeout_seconds * 1000)
            await asyncio.sleep(settings.scrape_polite_delay_seconds)
            links = await page.locator("a").evaluate_all(
                """els => els.map(a => ({
                    text: (a.innerText || '').trim(),
                    href: a.href || '',
                    parent: (a.closest('li, article, section, div')?.innerText || '').trim()
                }))"""
            )
            body_text = await page.locator("body").inner_text(timeout=5000)
            await browser.close()

        jobs: list[NormalizedJob] = []
        seen: set[str] = set()
        for item in links:
            title = clean_text(item.get("text"))
            context = clean_text(item.get("parent") or title)
            href = item.get("href") or ""
            url = urljoin(source.career_url, href)
            if not is_probable_job_link(title, url, context):
                continue
            if not is_region_compatible(f"{title} {context}"):
                continue
            key = f"{title}|{url}"
            if key in seen:
                continue
            seen.add(key)
            jobs.append(
                NormalizedJob(
                    source_name=source.company_name,
                    source_type=source.source_type,
                    company=source.company_name,
                    title=title[:500],
                    location=self._guess_location(context),
                    remote_type="remote" if "remote" in f"{title} {context}".lower() else None,
                    region=self._guess_region(context),
                    job_url=url,
                    description=context[:8000],
                    raw_source={"adapter": "generic_playwright", "snapshot": body_text[:12000]},
                )
            )
        return jobs[:100]

    def _guess_location(self, text: str) -> str | None:
        lowered = text.lower()
        for token in ["remote worldwide", "work from anywhere", "remote", "emea", "europe", "germany", "berlin", "london", "netherlands", "sweden", "uk", "france", "italy", "spain"]:
            if token in lowered:
                return token.title()
        return None

    def _guess_region(self, text: str) -> str | None:
        lowered = text.lower()
        if "work from anywhere" in lowered or "remote worldwide" in lowered or "anywhere" in lowered:
            return "Worldwide"
        if any(term in lowered for term in ["europe", "emea", "germany", "sweden", "uk", "united kingdom", "france", "italy", "spain", "netherlands"]):
            return "Europe"
        if "remote" in lowered:
            return "Remote"
        return None