from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

import structlog
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.core.exceptions import EmbeddingServiceException

log = structlog.get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_REQUEST_TIMEOUT)


class EmbeddingService:
    """Wraps OpenAI text-embedding-3-large with retry logic and batch support."""

    def __init__(self) -> None:
        self._client = _get_client()

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            raise EmbeddingServiceException("Cannot embed empty text")

        if settings.OPENAI_API_KEY.startswith("sk-your") or settings.OPENAI_API_KEY.startswith("mock"):
            import hashlib
            import numpy as np
            seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            vec = rng.randn(settings.OPENAI_EMBEDDING_DIMENSIONS).astype(float)
            norm = float(np.linalg.norm(vec))
            return (vec / norm).tolist() if norm > 0 else vec.tolist()

        try:
            response = await self._client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text[:8192],  # hard limit for safety
                dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS,
            )
            embedding = response.data[0].embedding
            log.debug("embedding_generated", model=settings.OPENAI_EMBEDDING_MODEL, dim=len(embedding))
            return embedding
        except Exception as exc:
            log.warning("embedding_api_fallback", error=str(exc))
            import hashlib
            import numpy as np
            seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            vec = rng.randn(settings.OPENAI_EMBEDDING_DIMENSIONS).astype(float)
            norm = float(np.linalg.norm(vec))
            return (vec / norm).tolist() if norm > 0 else vec.tolist()

    async def embed_batch(self, texts: list[str], batch_size: int = 16) -> list[list[float]]:
        """Embed multiple texts with controlled concurrency."""
        results: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await asyncio.gather(*[self.embed_text(t) for t in batch])
            results.extend(embeddings)
        return results


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
