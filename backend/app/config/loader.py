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


def config_path(filename: str) -> Path:
    return Path(get_settings().config_dir) / filename


def load_yaml(filename: str) -> Any:
    with config_path(filename).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_sources() -> list[SourceConfig]:
    raw = load_yaml("sources.yaml")
    return [SourceConfig.model_validate(item) for item in raw["sources"]]


def load_profile() -> dict[str, Any]:
    return load_yaml("profile.yaml")


def sync_sources(db: Session) -> None:
    for item in load_sources():
        existing = db.query(Source).filter(Source.company_name == item.company_name).one_or_none()
        values = item.model_dump(mode="json")
        values["career_url"] = str(item.career_url)
        if existing:
            for key, value in values.items():
                if key != "enabled":
                    setattr(existing, key, value)
        else:
            db.add(Source(**values))
    db.commit()
