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


class ContactAlreadyExistsError(ConflictError):
    """Raised when creating a contact whose email is already in the audience.

    HTTP 409 with ``error_code="resource_already_exists"`` on
    ``POST /audience/contacts``.

    This is a client-correctable condition, not an outage — **do not retry it.**
    Update the existing contact with ``client.audience.contacts.update()``, or
    use ``client.audience.contacts.bulk_create(..., update_existing=True)``.

    Older API versions surfaced this as an HTTP 500 with the misleading
    ``send_error`` code, which arrived as a :class:`ServerError`. Subclassing
    :class:`ConflictError` keeps existing ``except ConflictError`` and
    ``except LettrError`` handlers working unchanged.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        email: str | None = None,
    ) -> None:
        self.email = email
        """The address that collided, when the SDK knows it."""
        super().__init__(message, error_code)


class IdempotencyConflictError(ConflictError):
    """The ``Idempotency-Key`` was already used with a *different* payload.

    HTTP 409, ``error_code="idempotency_key_conflict"``.

    **Never retry this.** Two different emails were sent under one key, which is
    a bug on the caller's side; the same request will fail identically forever.
    Use a key that is unique per logical send, or send the payload the key was
    first used with.

    Keys are scoped per team *and* API key, so the same string sent through a
    different API key is a different key and will not collide.
    """


class IdempotencyInProgressError(ConflictError):
    """The original send for this ``Idempotency-Key`` is still processing.

    HTTP 409, ``error_code="idempotency_in_progress"``.

    Unlike :class:`IdempotencyConflictError` this **is** retryable, and must be
    retried with the *same* key - a fresh key would send a second email. Wait
    :attr:`retry_after` seconds first.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        """Seconds to wait before retrying, from the ``Retry-After`` header."""
        super().__init__(message, error_code)


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


def raise_for_status(
    status_code: int,
    body: Any,
    headers: Any | None = None,
) -> None:
    """Raise the appropriate exception based on the HTTP status code.

    ``headers`` is only consulted for ``Retry-After``, which is what separates
    the retryable idempotency conflict from the permanent one.
    """
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
        # The two idempotency conflicts need telling apart: one is safe to
        # retry with the same key, the other will fail forever.
        if error_code == "idempotency_in_progress":
            raise IdempotencyInProgressError(
                message=message,
                error_code=error_code,
                retry_after=_retry_after(headers),
            )

        if error_code == "idempotency_key_conflict":
            raise IdempotencyConflictError(message=message, error_code=error_code)

        raise ConflictError(message=message, error_code=error_code)

    if status_code == 422:
        raise ValidationError(message=message, errors=body.get("errors"))

    if status_code == 429:
        raise RateLimitError(message=message, error_code=error_code)

    if status_code >= 500:
        raise ServerError(message=message, error_code=error_code)

    raise LettrError(f"{message} (HTTP {status_code})")


def _retry_after(headers: Any | None) -> int | None:
    """Parse ``Retry-After`` into seconds, or None when absent or unusable."""
    if headers is None:
        return None

    try:
        value = headers.get("Retry-After")
    except AttributeError:
        return None

    if value is None:
        return None

    try:
        seconds = int(value)
    except (TypeError, ValueError):
        return None

    return seconds if seconds > 0 else None
