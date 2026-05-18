from app.config.loader import SourceConfig


def test_source_config_validation():
    source = SourceConfig.model_validate(
        {
            "company_name": "Example",
            "career_url": "https://example.com/jobs",
            "source_type": "company",
            "adapter_type": "static_html",
            "priority": "high",
            "enabled": True,
        }
    )
    assert source.company_name == "Example"
    assert str(source.career_url) == "https://example.com/jobs"
