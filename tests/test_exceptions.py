"""Tests for exception handling and raise_for_status."""

from __future__ import annotations

import pytest

from lettr._exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    LettrError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    raise_for_status,
)


class TestRaiseForStatus:
    def test_2xx_does_not_raise(self) -> None:
        raise_for_status(200, {"message": "ok"})
        raise_for_status(201, {"message": "created"})
        raise_for_status(204, None)

    def test_400_raises_bad_request(self) -> None:
        with pytest.raises(BadRequestError) as exc_info:
            raise_for_status(400, {"message": "bad", "error_code": "invalid_domain"})
        assert exc_info.value.message == "bad"
        assert exc_info.value.error_code == "invalid_domain"

    def test_401_raises_authentication_error(self) -> None:
        with pytest.raises(AuthenticationError) as exc_info:
            raise_for_status(401, {"message": "Unauthenticated"})
        assert exc_info.value.message == "Unauthenticated"

    def test_403_raises_forbidden_error(self) -> None:
        with pytest.raises(ForbiddenError) as exc_info:
            raise_for_status(403, {"message": "Forbidden"})
        assert exc_info.value.message == "Forbidden"

    def test_404_raises_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            raise_for_status(404, {"message": "Not found"})

    def test_409_raises_conflict(self) -> None:
        with pytest.raises(ConflictError):
            raise_for_status(409, {"message": "Already exists"})

    def test_422_raises_validation_error(self) -> None:
        body = {
            "message": "Validation failed",
            "errors": {"email": ["required"]},
        }
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(422, body)
        assert exc_info.value.errors == {"email": ["required"]}

    def test_422_without_errors_field(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            raise_for_status(422, {"message": "Invalid"})
        assert exc_info.value.errors == {}

    def test_429_raises_rate_limit_error(self) -> None:
        with pytest.raises(RateLimitError) as exc_info:
            raise_for_status(429, {"message": "Quota exceeded", "error_code": "quota_exceeded"})
        assert exc_info.value.error_code == "quota_exceeded"

    def test_500_raises_server_error(self) -> None:
        with pytest.raises(ServerError) as exc_info:
            raise_for_status(500, {"message": "Internal error", "error_code": "send_error"})
        assert exc_info.value.error_code == "send_error"

    def test_502_raises_server_error(self) -> None:
        with pytest.raises(ServerError):
            raise_for_status(502, {"message": "Bad gateway", "error_code": "transmission_failed"})

    def test_non_dict_body_raises_lettr_error(self) -> None:
        with pytest.raises(LettrError, match="Unexpected error"):
            raise_for_status(500, "not a dict")

    def test_unknown_status_raises_lettr_error(self) -> None:
        with pytest.raises(LettrError, match="HTTP 418"):
            raise_for_status(418, {"message": "I'm a teapot"})


class TestValidationErrorStr:
    def test_str_with_errors(self) -> None:
        err = ValidationError("Failed", errors={"name": ["required", "too short"]})
        assert "name: required, too short" in str(err)

    def test_str_without_errors(self) -> None:
        err = ValidationError("Failed")
        assert str(err) == "Failed"
