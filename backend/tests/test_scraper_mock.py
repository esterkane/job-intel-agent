import pytest

from app.scrapers.base import NormalizedJob, ScraperAdapter


class MockAdapter(ScraperAdapter):
    async def scrape(self, source):
        return [
            NormalizedJob(
                source_name=source.company_name,
                source_type=source.source_type,
                company=source.company_name,
                title="RAG Solutions Engineer",
                location="Remote Europe",
                remote_type="remote",
                region="Europe",
                job_url="https://example.com/jobs/1",
                description="RAG, retrieval, and customer automation.",
            )
        ]


@pytest.mark.asyncio
async def test_mocked_scraper_adapter():
    source = type("Source", (), {"company_name": "Example", "source_type": "company"})()
    jobs = await MockAdapter().scrape(source)
    assert jobs[0].title == "RAG Solutions Engineer"
