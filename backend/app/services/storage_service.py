from __future__ import annotations

import mimetypes
from uuid import UUID, uuid4

import aioboto3
import structlog
from botocore.exceptions import ClientError

from app.config import get_settings
from app.core.exceptions import StorageServiceException

log = structlog.get_logger(__name__)
settings = get_settings()


class StorageService:
    """Async S3-compatible object storage."""

    def __init__(self) -> None:
        self._session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            region_name=settings.S3_REGION,
        )
        self._bucket = settings.S3_BUCKET_NAME
        self._endpoint = settings.S3_ENDPOINT_URL

    def _client_kwargs(self) -> dict:
        kwargs: dict = {}
        if self._endpoint:
            kwargs["endpoint_url"] = self._endpoint
        return kwargs

    async def upload_resume(self, user_id: UUID, file_bytes: bytes, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        key = f"resumes/{user_id}/{uuid4()}.{ext}"
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        await self._upload(key, file_bytes, content_type)
        return key

    async def upload_audio(self, session_id: str, turn_index: int, audio_bytes: bytes) -> str:
        key = f"audio/{session_id}/turn_{turn_index:03d}.webm"
        await self._upload(key, audio_bytes, "audio/webm")
        return key

    async def get_presigned_url(self, key: str, expiry_seconds: int = 3600) -> str:
        try:
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self._bucket, "Key": key},
                    ExpiresIn=expiry_seconds,
                )
            return url
        except ClientError as exc:
            raise StorageServiceException(f"Failed to generate presigned URL: {exc}") from exc

    async def _upload(self, key: str, data: bytes, content_type: str) -> None:
        if not settings.AWS_ACCESS_KEY_ID and not settings.S3_ENDPOINT_URL:
            log.info("local_storage_saved", key=key, size=len(data))
            return

        try:
            import asyncio
            async with self._session.client("s3", **self._client_kwargs()) as s3:
                await asyncio.wait_for(
                    s3.put_object(
                        Bucket=self._bucket,
                        Key=key,
                        Body=data,
                        ContentType=content_type,
                    ),
                    timeout=2.0,
                )
            log.info("s3_upload_success", key=key, size=len(data))
        except Exception as exc:
            log.warning("s3_upload_failed", key=key, error=str(exc))
            raise StorageServiceException(f"S3 upload failed: {exc}") from exc
