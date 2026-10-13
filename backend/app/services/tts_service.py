from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import AsyncIterator, Literal

import structlog
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import LLMServiceException

log = structlog.get_logger(__name__)
settings = get_settings()

TtsVoice = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

_tts_quota_exhausted = False


def _should_retry_tts_call(exc: BaseException) -> bool:
    err_str = str(exc).lower()
    if "insufficient_quota" in err_str or "credit_balance_exhausted" in err_str:
        return False
    return True


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.OPENAI_REQUEST_TIMEOUT)


class TTSService:
    """OpenAI TTS: synthesizes interview questions to speech.

    Streams PCM audio chunks back so the frontend can play them in real-time
    over the WebSocket connection, giving a natural AI interviewer voice.
    """

    DEFAULT_VOICE: TtsVoice = "nova"
    MODEL = "tts-1"          # tts-1-hd for higher quality in production
    RESPONSE_FORMAT = "opus"  # Opus = low-latency streaming friendly

    def __init__(self) -> None:
        self._client = _get_client()

    @retry(
        retry=retry_if_exception(_should_retry_tts_call),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        reraise=True,
    )
    async def synthesize(
        self,
        text: str,
        voice: TtsVoice = DEFAULT_VOICE,
    ) -> bytes:
        """Return full audio bytes for a question text."""
        global _tts_quota_exhausted
        if _tts_quota_exhausted:
            raise LLMServiceException("OpenAI quota exhausted; fallback to browser speech synthesis.")

        if not text.strip():
            raise LLMServiceException("TTS input text is empty")
        try:
            response = await self._client.audio.speech.create(
                model=self.MODEL,
                voice=voice,
                input=text[:4096],
                response_format=self.RESPONSE_FORMAT,
            )
            audio_bytes = response.content
            log.info("tts_synthesized", chars=len(text), bytes=len(audio_bytes), voice=voice)
            return audio_bytes
        except Exception as exc:
            err_msg = str(exc)
            if "insufficient_quota" in err_msg or "credit_balance_exhausted" in err_msg:
                _tts_quota_exhausted = True
                log.warning("tts_quota_exhausted_fallback_enabled", error=err_msg)
            else:
                log.error("tts_failed", error=err_msg)
            raise LLMServiceException(f"TTS synthesis failed: {exc}") from exc

    async def stream_synthesis(
        self,
        text: str,
        voice: TtsVoice = DEFAULT_VOICE,
        chunk_size: int = 4096,
    ) -> AsyncIterator[bytes]:
        """Async-yield audio chunks for streaming over WebSocket."""
        global _tts_quota_exhausted
        if _tts_quota_exhausted or not text.strip():
            return
        try:
            async with self._client.audio.speech.with_streaming_response.create(
                model=self.MODEL,
                voice=voice,
                input=text[:4096],
                response_format=self.RESPONSE_FORMAT,
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=chunk_size):
                    if chunk:
                        yield chunk
        except Exception as exc:
            err_msg = str(exc)
            if "insufficient_quota" in err_msg or "credit_balance_exhausted" in err_msg:
                _tts_quota_exhausted = True
                log.warning("tts_stream_quota_exhausted", error=err_msg)
            else:
                log.error("tts_stream_failed", error=err_msg)
            raise LLMServiceException(f"TTS streaming failed: {exc}") from exc
