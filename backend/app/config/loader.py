from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.models import Source


class SourceConfig(BaseModel):
    company_name: str
    career_url: HttpUrl
    source_type: str = "company"
    adapter_type: str = "static_html"
    remote_policy_notes: str | None = None
    culture_notes: str | None = None
    priority: str = "medium"
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    enabled: bool = True


class JobPlatformConfig(BaseModel):
    name: str
    url: HttpUrl | None = None
    source_type: str
    enabled: bool | str = False
    note: str | None = None

    @property
    def is_enabled(self) -> bool:
        return self.enabled is True


def config_path(filename: str) -> Path:
    return Path(get_settings().config_dir) / filename


def load_yaml(filename: str) -> Any:
    with config_path(filename).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_sources() -> list[SourceConfig]:
    raw = load_yaml("sources.yaml")
    return [SourceConfig.model_validate(item) for item in raw["sources"]]


def load_profile() -> dict[str, Any]:
    search_profile = config_path("search_profile.yaml")
    if search_profile.exists():
        return load_yaml("search_profile.yaml")
    return load_yaml("profile.yaml")


def load_search_profile() -> dict[str, Any]:
    return load_profile()


def load_job_platforms() -> list[JobPlatformConfig]:
    path = config_path("job_platforms.yaml")
    if not path.exists():
        return []
    raw = load_yaml("job_platforms.yaml")
    return [JobPlatformConfig.model_validate(item) for item in raw["platforms"]]


def _platform_to_source(item: JobPlatformConfig, profile: dict[str, Any]) -> dict[str, Any]:
    keyword_groups = profile.get("keyword_groups", {})
    return {
        "company_name": item.name,
        "career_url": str(item.url or "https://example.invalid/manual-source"),
        "source_type": item.source_type,
        "adapter_type": item.source_type,
        "remote_policy_notes": item.note,
        "culture_notes": item.note,
        "priority": "high" if item.source_type in {"api_json", "rss_or_feed"} else "medium",
        "include_keywords": keyword_groups.get("positive_core", []) + keyword_groups.get("positive_background_fit", []),
        "exclude_keywords": keyword_groups.get("negative", []),
        "target_regions": profile.get("target_location_logic", []),
        "enabled": item.is_enabled,
    }


def sync_sources(db: Session) -> None:
    platforms = load_job_platforms()
    if platforms:
        profile = load_profile()
        names = {item.name for item in platforms}
        db.query(Source).filter(Source.company_name.notin_(names)).update({Source.enabled: False}, synchronize_session=False)
        items = [_platform_to_source(item, profile) for item in platforms]
    else:
        items = []
        for item in load_sources():
            values = item.model_dump(mode="json")
            values["career_url"] = str(item.career_url)
            items.append(values)

    for values in items:
        existing = db.query(Source).filter(Source.company_name == values["company_name"]).one_or_none()
        if existing:
            for key, value in values.items():
                if platforms or key != "enabled":
                    setattr(existing, key, value)
        else:
            db.add(Source(**values))
    db.commit()
