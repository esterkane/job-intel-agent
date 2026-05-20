# Sources

Platform sources are configured in `config/job_platforms.yaml`. Company sources can still live in `config/sources.yaml`, but the MVP now treats job platforms as the primary registry.

Source categories:

- `api_json`: official or public JSON endpoints, enabled when appropriate. Arbeitnow and Working Nomads use this path.
- `public_static`: public unauthenticated HTML pages fetched politely with `httpx` and BeautifulSoup.
- `public_playwright`: public unauthenticated JavaScript pages opened with Playwright. No login, CAPTCHA bypass, or proxy rotation.
- `rss_or_feed`: reserved for feed-first sources.
- `jobspy_optional`: disabled by default and only for low-volume allowed use.
- `manual_browser_only`: saved-search/manual capture workflow only.
- `disabled_due_to_terms`: visible as a reference but never scraped.

Manual-only sources include LinkedIn, Indeed, Glassdoor, FlexJobs, Wellfound, PowerToFly, and XING. Use saved searches, job alerts, or Manual Capture; the app does not automate extraction from logged-in or restricted pages.
