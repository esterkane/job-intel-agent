import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CONFIG_DIR"] = str(Path(__file__).resolve().parents[2] / "config")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import SessionLocal, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Job  # noqa: E402


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_basic_job_api():
    init_db()
    db = SessionLocal()
    db.add(
        Job(
            source_name="Test",
            source_type="company",
            company="Grafana Labs",
            title="Observability Architect",
            location="Remote Europe",
            remote_type="remote",
            region="Europe",
            job_url="https://example.com/job",
            description="Customer advisory and OpenTelemetry",
            content_hash="abc",
            final_score=88,
            score_breakdown={"remote_fit_score": 95},
        )
    )
    db.commit()
    db.close()
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert response.json()[0]["company"] == "Grafana Labs"
