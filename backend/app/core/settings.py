from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./jobintel.db"
    app_timezone: str = "Europe/Berlin"
    daily_scrape_time: str = "07:00"
    scrape_enabled: bool = True
    scrape_timeout_seconds: int = 45
    scrape_polite_delay_seconds: int = 2
    expire_missing_after_days: int = 21

    qdrant_enabled: bool = False
    qdrant_url: str = "http://qdrant:6333"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    llm_provider: str = "none"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    config_dir: str = "/app/config"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
