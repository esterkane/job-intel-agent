from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import quote_plus


TARGET_ROLE_FAMILIES = [
    "AI Search / RAG Backend Engineer",
    "Knowledge Systems Engineer",
    "Agentic Workflow Engineer",
    "Search / RAG Solutions Engineer",
    "AI Automation Engineer",
    "Support Workflow Modernization Engineer",
]

ENGLISH_QUERY_PHRASES = [
    "AI Search Engineer",
    "RAG Engineer",
    "Retrieval Engineer",
    "Search Backend Engineer",
    "Vector Search Engineer",
    "Semantic Search Engineer",
    "Knowledge Systems Engineer",
    "Knowledge Platform Engineer",
    "Agentic Workflow Engineer",
    "AI Workflow Engineer",
    "AI Automation Engineer",
    "Support Automation Engineer",
    "Customer Automation Engineer",
    "Technical Solutions Engineer AI",
    "Solutions Engineer Search",
    "Forward Deployed Engineer AI",
    "Developer Advocate Search AI",
    "Technical Writer Search AI",
    "KCS Knowledge Manager",
    "Knowledge Operations Engineer",
]

GERMAN_QUERY_PHRASES = [
    "KI Engineer",
    "AI Engineer",
    "Suchtechnologie",
    "Search Engineer",
    "Knowledge Manager",
    "Wissensmanagement",
    "Automatisierung Support",
    "Support Automation",
    "Technical Consultant AI",
    "Solution Engineer AI",
    "Kundenautomatisierung",
    "Technischer Berater KI",
    "Wissensdatenbank",
    "Dokumentation AI",
    "RAG",
    "Vector Search",
    "Elasticsearch",
]

NEGATIVE_KEYWORDS = [
    "helpdesk",
    "desktop support",
    "onsite only",
    "24/7",
    "shift work",
    "call center",
]

BOOLEAN_BASE_QUERY = (
    '("RAG" OR "retrieval" OR "vector search" OR "semantic search" OR "hybrid search" '
    'OR "Elasticsearch" OR "knowledge systems" OR "AI agents" OR "agentic workflow" '
    'OR "support automation" OR "workflow automation") AND ("remote" OR "Germany" OR '
    '"Europe" OR "EU" OR "DACH") NOT ("helpdesk" OR "desktop support" OR "onsite only" '
    'OR "24/7" OR "shift work" OR "call center")'
)

API_FILTER_LOCALLY_PLATFORMS = {
    "Arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "Working Nomads": "https://www.workingnomads.com/api/exposed_jobs/",
}

MANUAL_ONLY_PLATFORMS = [
    "LinkedIn",
    "Indeed",
    "Glassdoor",
    "FlexJobs",
    "Wellfound",
    "PowerToFly",
    "XING",
]


@dataclass(frozen=True)
class SearchQueryVariant:
    id: str
    platform: str
    query_name: str
    role_family: str
    query: str
    language: str
    query_type: str
    mode: str
    url: str | None
    supported_features: list[str]
    negative_keywords: list[str]
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def build_search_strategy() -> list[dict]:
    variants: list[SearchQueryVariant] = []
    variants.extend(_api_filter_locally_queries())
    variants.extend(_englishjobs_queries())
    variants.extend(_devjobs_queries())
    variants.extend(_instaffo_queries())
    variants.extend(_stepstone_queries())
    variants.extend(_manual_platform_queries())
    return [variant.to_dict() for variant in variants]


def _api_filter_locally_queries() -> list[SearchQueryVariant]:
    variants: list[SearchQueryVariant] = []
    for platform, url in API_FILTER_LOCALLY_PLATFORMS.items():
        variants.append(SearchQueryVariant(
            id=_id(platform, "api-local-filter", "boolean-base"),
            platform=platform,
            query_name="Fetch broadly, filter locally",
            role_family="All target role families",
            query=BOOLEAN_BASE_QUERY,
            language="mixed",
            query_type="local_filter_boolean",
            mode="api_filter_locally",
            url=url,
            supported_features=["api_ingestion", "local_positive_keywords", "local_negative_keywords", "remote_region_filter"],
            negative_keywords=NEGATIVE_KEYWORDS,
        ))
    return variants


def _englishjobs_queries() -> list[SearchQueryVariant]:
    phrases = [
        "remote AI Engineer",
        "remote Search Engineer",
        "remote Solutions Engineer",
        "remote Knowledge Manager",
    ]
    return [
        _public_url_variant("EnglishJobs.de", phrase, _role_family_for(phrase), phrase, "English", "public_search_url",
                            f"https://englishjobs.de/jobs/remote?q={quote_plus(phrase)}")
        for phrase in phrases
    ]


def _devjobs_queries() -> list[SearchQueryVariant]:
    tech_terms = ["Python AI", "Docker AI", "Kubernetes AI", "Elasticsearch", "React TypeScript AI", "Claude n8n Puppeteer automation"]
    return [
        _public_url_variant("DEVjobs.de", term, _role_family_for(term), term, "mixed", "tech_stack_query",
                            f"https://en.devjobs.de/jobs/{quote_plus(term).replace('+', '-').lower()}")
        for term in tech_terms
    ]


def _instaffo_queries() -> list[SearchQueryVariant]:
    categories = [
        ("Software Engineering + AI/RAG", "Software Engineering", "AI RAG Software Engineering"),
        ("Data + Search", "Data", "Data Search Elasticsearch RAG"),
        ("IT-Infrastructure + AI automation", "IT-Infrastructure", "Kubernetes Docker AI automation"),
        ("Consulting + AI automation", "Consulting", "Consulting AI automation"),
        ("Product + knowledge systems", "Product", "Product knowledge systems AI"),
    ]
    variants: list[SearchQueryVariant] = []
    for name, category, query in categories:
        variants.append(_public_url_variant(
            "Instaffo",
            name,
            _role_family_for(query),
            f"{category}: {query}",
            "mixed",
            "category_filter_query",
            f"https://jobs.instaffo.com/en/jobs/find?query={quote_plus(query)}",
        ))
    return variants


def _stepstone_queries() -> list[SearchQueryVariant]:
    phrases = ["RAG Engineer", "AI Engineer", "Solution Engineer AI", "Knowledge Manager", "Technical Consultant AI", "Support Automation"]
    return [
        SearchQueryVariant(
            id=_id("StepStone", "manual-public", phrase),
            platform="StepStone",
            query_name=phrase,
            role_family=_role_family_for(phrase),
            query=_with_negative_hint(phrase),
            language=_language_for(phrase),
            query_type="manual_public_search_url",
            mode="manual_only",
            url=f"https://www.stepstone.de/jobs/{quote_plus(phrase).replace('+', '-').lower()}?radius=30&searchOrigin=Resultlist_top-search&where=Home-Office",
            supported_features=["saved_search_url", "home_office_filter_hint", "manual_review"],
            negative_keywords=NEGATIVE_KEYWORDS,
        )
        for phrase in phrases
    ]


def _manual_platform_queries() -> list[SearchQueryVariant]:
    variants: list[SearchQueryVariant] = []
    for platform in MANUAL_ONLY_PLATFORMS:
        for phrase in ENGLISH_QUERY_PHRASES + GERMAN_QUERY_PHRASES:
            variants.append(SearchQueryVariant(
                id=_id(platform, "manual-saved-search", phrase),
                platform=platform,
                query_name=phrase,
                role_family=_role_family_for(phrase),
                query=_with_negative_hint(phrase),
                language=_language_for(phrase),
                query_type="saved_search_url",
                mode="manual_only",
                url=_manual_search_url(platform, phrase),
                supported_features=["saved_search_url", "manual_review", "manual_capture"],
                negative_keywords=NEGATIVE_KEYWORDS if platform in {"LinkedIn", "Indeed", "Glassdoor", "XING"} else [],
            ))
    return variants


def _public_url_variant(platform: str, name: str, role_family: str, query: str, language: str, query_type: str, url: str) -> SearchQueryVariant:
    return SearchQueryVariant(
        id=_id(platform, query_type, name),
        platform=platform,
        query_name=name,
        role_family=role_family,
        query=_with_negative_hint(query),
        language=language,
        query_type=query_type,
        mode="public_scrape_or_manual",
        url=url,
        supported_features=["public_search_url", "local_filtering", "manual_review"],
        negative_keywords=NEGATIVE_KEYWORDS,
    )


def _manual_search_url(platform: str, phrase: str) -> str:
    q = quote_plus(phrase)
    if platform == "LinkedIn":
        return f"https://www.linkedin.com/jobs/search/?keywords={q}&location=Germany&f_WT=2"
    if platform == "Indeed":
        return f"https://de.indeed.com/jobs?q={q}&l=Germany&sc=0kf%3Aattr%28DSQF7%29%3B"
    if platform == "Glassdoor":
        slug = quote_plus(f"germany {phrase} remote").replace("+", "-").lower()
        return f"https://www.glassdoor.com/Job/{slug}-jobs-SRCH.htm"
    if platform == "FlexJobs":
        return f"https://www.flexjobs.com/search?search={q}"
    if platform == "Wellfound":
        return f"https://wellfound.com/jobs?keyword={q}&remote=true"
    if platform == "PowerToFly":
        return f"https://powertofly.com/jobs/?keywords={q}&location=Remote"
    if platform == "XING":
        return f"https://www.xing.com/jobs/search?keywords={q}&location=Germany"
    return ""


def _with_negative_hint(query: str) -> str:
    negative_clause = " OR ".join(f'"{term}"' for term in NEGATIVE_KEYWORDS)
    return f"{query} NOT ({negative_clause})"


def _language_for(phrase: str) -> str:
    return "German" if phrase in GERMAN_QUERY_PHRASES or any(term in phrase for term in ["KI", "Wissens", "Kunden", "Berater", "Suchtechnologie"]) else "English"


def _role_family_for(phrase: str) -> str:
    value = phrase.lower()
    if "support" in value:
        return "Support Workflow Modernization Engineer"
    if any(term in value for term in ["rag", "retrieval", "search", "elasticsearch", "vector", "semantic", "suchtechnologie"]):
        return "AI Search / RAG Backend Engineer"
    if any(term in value for term in ["knowledge", "wissens", "kcs"]):
        return "Knowledge Systems Engineer"
    if any(term in value for term in ["agent", "workflow", "n8n", "puppeteer", "automation", "automatisierung"]):
        return "Agentic Workflow Engineer"
    if any(term in value for term in ["solution", "solutions", "consultant", "berater", "consulting"]):
        return "Search / RAG Solutions Engineer"
    if "ai" in value or "ki" in value:
        return "AI Automation Engineer"
    return "AI Search / RAG Backend Engineer"


def _id(platform: str, kind: str, value: str) -> str:
    raw = f"{platform}-{kind}-{value}".lower()
    return "".join(char if char.isalnum() else "-" for char in raw).strip("-")
