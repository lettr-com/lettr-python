"""Lettr API exceptions."""

from __future__ import annotations

from typing import Any


class LettrError(Exception):
    """Base exception for all Lettr errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AuthenticationError(LettrError):
    """Raised when the API key is missing or invalid (401)."""


class ForbiddenError(LettrError):
    """Raised when access is forbidden (403)."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)


class ValidationError(LettrError):
    """Raised when request validation fails (422)."""

    def __init__(
        self,
        message: str,
        errors: dict[str, list[str]] | None = None,
    ) -> None:
        self.errors = errors or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.errors:
            details = "; ".join(
                f"{field}: {', '.join(msgs)}" for field, msgs in self.errors.items()
            )
            return f"{self.message} ({details})"
        return self.message


class NotFoundError(LettrError):
    """Raised when a resource is not found (404)."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)


class ConflictError(LettrError):
    """Raised when a resource already exists (409)."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)


class BadRequestError(LettrError):
    """Raised for client-side errors (400)."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)


class RateLimitError(LettrError):
    """Raised when rate limit or quota is exceeded (429)."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)


class ServerError(LettrError):
    """Raised for server-side errors (500, 502)."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.error_code = error_code
        super().__init__(message)


def raise_for_status(status_code: int, body: Any) -> None:
    """Raise the appropriate exception based on the HTTP status code."""
    if 200 <= status_code < 300:
        return

    if not isinstance(body, dict):
        raise LettrError(f"Unexpected error (HTTP {status_code})")

    message = body.get("message", "Unknown error")
    error_code = body.get("error_code")

    if status_code == 400:
        raise BadRequestError(message=message, error_code=error_code)

    if status_code == 401:
        raise AuthenticationError(message)

    if status_code == 403:
        raise ForbiddenError(message=message, error_code=error_code)

    if status_code == 404:
        raise NotFoundError(message=message, error_code=error_code)

    if status_code == 409:
        raise ConflictError(message=message, error_code=error_code)

    if status_code == 422:
        raise ValidationError(message=message, errors=body.get("errors"))

    if status_code == 429:
        raise RateLimitError(message=message, error_code=error_code)

    if status_code >= 500:
        raise ServerError(message=message, error_code=error_code)

    raise LettrError(f"{message} (HTTP {status_code})")
