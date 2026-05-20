import re
from urllib.parse import urlparse

JOB_TITLE_TERMS = (
    "engineer", "architect", "manager", "lead", "director", "advocate", "writer", "specialist",
    "consultant", "success", "solutions", "solution", "enablement", "education", "operations",
    "account", "deployed", "forward", "technical", "relevance", "search", "rag", "ai",
)

JOB_URL_TERMS = (
    "job", "jobs", "career", "careers", "opening", "openings", "position", "positions",
    "greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "smartrecruiters.com",
)

BLOCKED_LINK_TERMS = (
    "skip to", "privacy", "cookie", "terms", "security", "youtube", "gmail", "blog", "changelog",
    "docs", "documentation", "guide", "guides", "customer stories", "case studies", "events",
    "academy", "community", "request accommodation", "google privacy policy", "start building",
    "get a demo", "support", "availability", "research", "haiku", "alternatives",
)

BLOCKED_REGION_TERMS = (
    "remote united states", "remote-friendly, united states", "united states (remote)", "united states", "remote-us", "remote us", "remote-utah",
    "usa", " us ", "| us |", "| usa |", "east coast", "west coast", "central | remote united states",
    "pst", "est", "cst", "pacific time", "eastern time", "north america only", "americas only",
    "canada", "remote canada", "toronto", "utah", "california", "texas", "san francisco",
    "new york", "nyc", "austin", "dallas", "chicago", "raleigh", "charlotte", "seattle",
    "phoenix", "atlanta", "los angeles", "san diego", "las vegas", "denver", "boston",
    "salt lake city", "washington dc", "japan", "tokyo", "apac", "australia", "sydney", "singapore",
    "remote united kingdom", "united kingdom (remote)", "uk only", "london", "amsterdam",
)

REMOTE_TERMS = (
    "remote", "remote-friendly", "remote friendly", "distributed", "remote-first", "remote first",
)

REMOTE_GERMANY_EUROPE_TERMS = (
    "remote germany", "germany remote", "germany (remote)", "remote deutschland",
    "remote europe", "europe remote", "europe (remote)", "remote - europe", "remote, europe",
    "remote emea", "emea remote", "emea (remote)", "remote - emea", "remote, emea",
    "remote eu", "eu remote", "eu (remote)", "remote - eu", "remote, eu",
    "remote cet", "cet remote", "remote cest", "cest remote", "central european remote",
    "remote utc+0", "remote utc+1", "remote utc+2", "remote utc+3",
    "remote gmt+0", "remote gmt+1", "remote gmt+2", "remote gmt+3",
)

US_STATE_RE = re.compile(
    r",\s*(al|ak|az|ar|ca|co|ct|dc|de|fl|ga|hi|ia|id|il|in|ks|ky|la|ma|md|me|mi|mn|mo|ms|mt|nc|nd|ne|nh|nj|nm|nv|ny|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|va|vt|wa|wi|wv|wy)\b"
)


def clean_text(value: str | None) -> str:
    return " ".join((value or "").split())


def is_probable_job_link(title: str, url: str, context: str = "") -> bool:
    title_clean = clean_text(title)
    haystack = f"{title_clean} {url} {context}".lower()
    if len(title_clean) < 8 or len(title_clean) > 180:
        return False
    if any(term in haystack for term in BLOCKED_LINK_TERMS):
        return False
    if not any(term in haystack for term in JOB_URL_TERMS):
        return False
    return any(term in title_clean.lower() for term in JOB_TITLE_TERMS)


def is_region_compatible(text: str) -> bool:
    normalized = f" {clean_text(text).lower()} "
    if US_STATE_RE.search(normalized):
        return False
    if any(term in normalized for term in BLOCKED_REGION_TERMS):
        return False
    if any(term in normalized for term in REMOTE_GERMANY_EUROPE_TERMS):
        return True
    is_worldwide = any(term in normalized for term in [
        "work from anywhere", "remote worldwide", "anywhere in the world", "global remote", "remote anywhere",
    ])
    if is_worldwide:
        return any(term in normalized for term in ["germany", "europe", " eu ", "emea", "cet", "cest"])
    if "hybrid" in normalized and any(city in normalized for city in ["munich", "augsburg", "muenchen", "münchen"]):
        return True
    return False


def host_matches(url: str, allowed_hosts: tuple[str, ...]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts)
