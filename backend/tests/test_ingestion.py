from app.scrapers.base import NormalizedJob
from app.services.ingestion import content_hash


def test_content_hash_changes_with_job_content():
    base = NormalizedJob(
        source_name="Grafana",
        source_type="company",
        company="Grafana",
        title="Observability Architect",
        location="Remote Europe",
        remote_type="remote",
        region="Europe",
        job_url="https://example.com/a",
        description="OpenTelemetry and customer advisory",
    )
    changed = NormalizedJob(**{**base.__dict__, "description": "Different"})
    assert content_hash(base) != content_hash(changed)
