import httpx

from app.core.settings import get_settings


async def optional_summary(prompt: str) -> str | None:
    settings = get_settings()
    if settings.llm_provider == "none":
        return None
    if settings.llm_provider == "ollama":
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={"model": settings.ollama_model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                return response.json().get("response")
        except Exception:
            return None
    if settings.llm_provider == "openai":
        # Optional placeholder: intentionally disabled unless the user adds API billing credentials.
        return None
    return None
