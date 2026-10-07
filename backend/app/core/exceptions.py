from __future__ import annotations

from http import HTTPStatus
from typing import Any


class AppBaseException(Exception):
    """Root exception for all application-defined errors."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.details = details
        self.headers = headers
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload


# ── 400 Bad Request ────────────────────────────────────────────────────────────
class BadRequestException(AppBaseException):
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "Bad request"


class ValidationException(AppBaseException):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed"


class FileTooLargeException(AppBaseException):
    status_code = HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    error_code = "FILE_TOO_LARGE"
    message = "Uploaded file exceeds the size limit"


class UnsupportedFileTypeException(AppBaseException):
    status_code = HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    error_code = "UNSUPPORTED_FILE_TYPE"
    message = "File type is not supported"


class InvalidAudioException(AppBaseException):
    status_code = HTTPStatus.BAD_REQUEST
    error_code = "INVALID_AUDIO"
    message = "Audio data is malformed or unreadable"


# ── 401 / 403 ─────────────────────────────────────────────────────────────────
class AuthenticationException(AppBaseException):
    status_code = HTTPStatus.UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication credentials are invalid or expired"
    headers = {"WWW-Authenticate": "Bearer"}  # type: ignore[assignment]


class PermissionDeniedException(AppBaseException):
    status_code = HTTPStatus.FORBIDDEN
    error_code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action"


class ForbiddenException(PermissionDeniedException):
    pass


# ── 404 Not Found ─────────────────────────────────────────────────────────────
class NotFoundException(AppBaseException):
    status_code = HTTPStatus.NOT_FOUND
    error_code = "NOT_FOUND"
    message = "The requested resource was not found"


class ResumeNotFoundException(NotFoundException):
    error_code = "RESUME_NOT_FOUND"
    message = "Resume not found"


class JobDescriptionNotFoundException(NotFoundException):
    error_code = "JD_NOT_FOUND"
    message = "Job description not found"


class SessionNotFoundException(NotFoundException):
    error_code = "SESSION_NOT_FOUND"
    message = "Interview session not found"


# ── 409 Conflict ──────────────────────────────────────────────────────────────
class ConflictException(AppBaseException):
    status_code = HTTPStatus.CONFLICT
    error_code = "CONFLICT"
    message = "Resource conflict"


class DuplicateAtsAnalysisException(ConflictException):
    error_code = "DUPLICATE_ATS_ANALYSIS"
    message = "An ATS analysis for this resume and job description already exists"


# ── 422 Business Logic ────────────────────────────────────────────────────────
class SessionNotActiveException(AppBaseException):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "SESSION_NOT_ACTIVE"
    message = "Interview session is not in an active state"


class MaxQuestionsReachedException(AppBaseException):
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = "MAX_QUESTIONS_REACHED"
    message = "Session has reached the maximum number of questions"


# ── 502 Upstream ──────────────────────────────────────────────────────────────
class EmbeddingServiceException(AppBaseException):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "EMBEDDING_SERVICE_ERROR"
    message = "Embedding service returned an unexpected response"


class LLMServiceException(AppBaseException):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "LLM_SERVICE_ERROR"
    message = "LLM service returned an unexpected response"


class WhisperServiceException(AppBaseException):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "WHISPER_SERVICE_ERROR"
    message = "Transcription service returned an unexpected response"


class StorageServiceException(AppBaseException):
    status_code = HTTPStatus.BAD_GATEWAY
    error_code = "STORAGE_SERVICE_ERROR"
    message = "Object storage service returned an unexpected response"


# ── 429 / 503 Resilience & Governance ──────────────────────────────────────────
class RateLimitExceededException(AppBaseException):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded. Please wait before submitting more requests."


class QuotaExceededException(AppBaseException):
    status_code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = "AI_QUOTA_EXCEEDED"
    message = "Monthly AI budget limit has been reached for your organization."


class CircuitBreakerOpenException(AppBaseException):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = "CIRCUIT_BREAKER_OPEN"
    message = "Upstream service is temporarily unavailable due to error threshold."
