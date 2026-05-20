from functools import lru_cache
from math import sqrt

from app.config.loader import load_profile
from app.core.settings import get_settings


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(get_settings().embedding_model)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sqrt(sum(x * x for x in a))
    mag_b = sqrt(sum(y * y for y in b))
    if not mag_a or not mag_b:
        return 0
    return dot / (mag_a * mag_b)


def semantic_match(job_text: str) -> tuple[list[float] | None, float | None]:
    try:
        profile_text = load_profile().get("target_profile_text", "")
        if not profile_text.strip():
            return None, None
        model = _model()
        vectors = model.encode([profile_text, job_text], normalize_embeddings=True).tolist()
        semantic_score = round(max(0, _cosine(vectors[0], vectors[1])) * 100, 1)
        return vectors[1], semantic_score
    except Exception:
        return None, None


def upsert_qdrant(job_id: int, vector: list[float] | None, payload: dict) -> None:
    settings = get_settings()
    if not settings.qdrant_enabled or not vector:
        return
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, PointStruct, VectorParams

        client = QdrantClient(url=settings.qdrant_url)
        collection = "jobs"
        existing = [item.name for item in client.get_collections().collections]
        if collection not in existing:
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=len(vector), distance=Distance.COSINE),
            )
        client.upsert(
            collection_name=collection,
            points=[PointStruct(id=job_id, vector=vector, payload=payload)],
        )
    except Exception:
        return
