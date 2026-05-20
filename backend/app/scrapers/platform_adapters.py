from __future__ import annotations

import asyncio
from html import unescape
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import NormalizedJob, ScraperAdapter
from app.scrapers.filters import clean_text, is_probable_job_link, is_region_compatible


SEARCH_TERMS = (
    "rag", "retrieval", "search", "vector", "semantic", "elasticsearch", "opensearch",
    "knowledge", "kcs", "agent", "workflow", "automation", "solutions", "technical",
    "enablement", "developer advocate", "technical writer", "support automation",
)


def _matches_profile(title: str, description: str, location: str | None) -> bool:
    text = f"{title} {description} {location or ''}".lower()
    return any(term in text for term in SEARCH_TERMS) and is_region_compatible(text)


def _remote_type(value: str | None, description: str = "") -> str | None:
    text = f"{value or ''} {description}".lower()
    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    return None


def _as_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(str(item) for item in value.values())
    return str(value or "")


class ArbeitnowAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(source.career_url, headers={"User-Agent": "job-intel-agent/0.1 local research"})
            response.raise_for_status()
        payload = response.json()
        items = payload.get("data", payload if isinstance(payload, list) else [])
        jobs: list[NormalizedJob] = []
        for item in items:
            title = clean_text(item.get("title") or "")
            description = clean_text(BeautifulSoup(unescape(item.get("description") or ""), "html.parser").get_text(" ", strip=True))
            location = clean_text(item.get("location") or ("Remote" if item.get("remote") else ""))
            if not title or not _matches_profile(title, description, location):
                continue
            jobs.append(NormalizedJob(
                source_name=source.company_name,
                source_type=source.source_type,
                company=clean_text(item.get("company_name") or item.get("company") or source.company_name),
                title=title,
                location=location or None,
                remote_type="remote" if item.get("remote") else _remote_type(location, description),
                region="Germany/EU" if is_region_compatible(f"{title} {location} {description}") else None,
                job_url=item.get("url") or item.get("job_url") or source.career_url,
                description=description[:12000],
                department=clean_text(item.get("category") or "") or None,
                employment_type=clean_text(_as_text(item.get("job_types") or item.get("type") or "")) or None,
                raw_source={"adapter": "arbeitnow", "payload": item},
            ))
        return jobs[:100]


class WorkingNomadsAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(source.career_url, headers={"User-Agent": "job-intel-agent/0.1 local research"})
            response.raise_for_status()
        items = response.json()
        jobs: list[NormalizedJob] = []
        for item in (items if isinstance(items, list) else []):
            title = clean_text(item.get("title") or "")
            description = clean_text(BeautifulSoup(unescape(item.get("description") or ""), "html.parser").get_text(" ", strip=True))
            location = clean_text(_as_text(item.get("location") or item.get("locations") or "Remote"))
            if not title or not _matches_profile(title, description, location):
                continue
            jobs.append(NormalizedJob(
                source_name=source.company_name,
                source_type=source.source_type,
                company=clean_text(item.get("company") or source.company_name),
                title=title,
                location=location or None,
                remote_type=_remote_type(location, description) or "remote",
                region="Germany/EU" if is_region_compatible(f"{title} {location} {description}") else None,
                job_url=item.get("url") or item.get("apply_url") or source.career_url,
                description=description[:12000],
                department=clean_text(item.get("category_name") or item.get("category") or "") or None,
                employment_type=clean_text(item.get("job_type") or "") or None,
                raw_source={"adapter": "working_nomads", "payload": item},
            ))
        return jobs[:100]


class PublicStaticAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(source.career_url, headers={"User-Agent": "job-intel-agent/0.1 polite local research"})
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return _extract_links(source, soup, source.career_url, "public_static")


class PublicPlaywrightAdapter(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:  # pragma: no cover - depends on optional image dependency
            raise RuntimeError("Playwright is not available in this container image.") from exc

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page(user_agent="job-intel-agent/0.1 polite local research")
            await page.goto(source.career_url, wait_until="networkidle", timeout=45000)
            await asyncio.sleep(2)
            html = await page.content()
            await browser.close()
        soup = BeautifulSoup(html, "html.parser")
        return _extract_links(source, soup, source.career_url, "public_playwright")


class ManualBrowserSource(ScraperAdapter):
    async def scrape(self, source) -> list[NormalizedJob]:
        return []


def _extract_links(source, soup: BeautifulSoup, base_url: str, adapter: str) -> list[NormalizedJob]:
    jobs: list[NormalizedJob] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=True):
        title = clean_text(link.get_text(" ", strip=True))
        parent = link.find_parent(["li", "article", "section", "div"])
        context = clean_text(parent.get_text(" ", strip=True) if parent else title)
        url = urljoin(base_url, link["href"])
        if not is_probable_job_link(title, url, context):
            continue
        if not _matches_profile(title, context, context):
            continue
        key = f"{title}|{url}"
        if key in seen:
            continue
        seen.add(key)
        jobs.append(NormalizedJob(
            source_name=source.company_name,
            source_type=source.source_type,
            company=source.company_name,
            title=title[:500],
            location=_guess_location(context),
            remote_type=_remote_type(context),
            region="Germany/EU",
            job_url=url,
            description=context[:12000],
            raw_source={"adapter": adapter, "snapshot": soup.get_text(" ", strip=True)[:12000]},
        ))
    return jobs[:80]


def _guess_location(text: str) -> str | None:
    lowered = text.lower()
    for token in ["remote germany", "remote europe", "remote emea", "germany", "europe", "emea", "remote", "munich", "augsburg"]:
        if token in lowered:
            return token.title()
    return None
