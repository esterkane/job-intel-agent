from dataclasses import dataclass, field


@dataclass
class NormalizedJob:
    source_name: str
    source_type: str
    company: str
    title: str
    location: str | None
    remote_type: str | None
    region: str | None
    job_url: str
    description: str | None = None
    department: str | None = None
    employment_type: str | None = None
    raw_source: dict = field(default_factory=dict)


class ScraperAdapter:
    async def scrape(self, source) -> list[NormalizedJob]:
        raise NotImplementedError
