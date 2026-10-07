from __future__ import annotations

import asyncio
import io
from functools import lru_cache

import structlog
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import WhisperServiceException

log = structlog.get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_REQUEST_TIMEOUT)


class WhisperClient:
    """Submits audio to Whisper API and returns transcript with timing data."""

    def __init__(self) -> None:
        self._client = _get_client()

    def _is_mock_env(self) -> bool:
        key = settings.OPENAI_API_KEY or ""
        return (
            not key
            or key.startswith("sk-your")
            or key.startswith("mock")
            or "mock" in key.lower()
            or len(key) < 20
        )

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """Transcribe a complete audio buffer."""
        if len(audio_bytes) < 100:
            raise WhisperServiceException("Audio buffer too small for transcription")

        if self._is_mock_env():
            # In testing or offline environments, produce deterministic simulated candidate response
            return (
                "In our production microservices system, we implement distributed caching with Redis Sentinel. "
                "We use the transactional outbox pattern with Kafka and PostgreSQL to ensure consistency, "
                "handling network partitions with circuit breakers and optimistic locking."
            )

        try:
            file_obj = io.BytesIO(audio_bytes)
            file_obj.name = "audio.webm"
            response = await self._client.audio.transcriptions.create(
                model=settings.OPENAI_WHISPER_MODEL,
                file=file_obj,
                language=language,
                response_format="text",
            )
            transcript = str(response).strip()
            log.info("whisper_transcription_complete", chars=len(transcript))
            return transcript
        except Exception as exc:
            log.error("whisper_failed", error=str(exc))
            raise WhisperServiceException(f"Whisper API error: {exc}") from exc

    async def transcribe_chunks_streaming(
        self,
        chunk_iterator: asyncio.Queue[bytes | None],
        on_partial: asyncio.Queue[str],
        language: str = "en",
    ) -> bytes:
        """Accumulate audio chunks, transcribe each window, push partials.
        Returns the full audio buffer.
        """
        buffer = bytearray()
        window = bytearray()
        window_size = settings.AUDIO_CHUNK_DURATION_MS * settings.AUDIO_SAMPLE_RATE // 1000 * 2

        while True:
            chunk = await chunk_iterator.get()
            if chunk is None:  # Sentinel: end of stream
                break
            buffer.extend(chunk)
            window.extend(chunk)

            if len(window) >= window_size:
                try:
                    partial = await self.transcribe(bytes(window), language=language)
                    await on_partial.put(partial)
                    window.clear()
                except WhisperServiceException:
                    pass  # Drop failed partial, continue accumulating

        return bytes(buffer)
