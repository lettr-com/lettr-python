"""Tests for idempotent sends."""

from __future__ import annotations

import httpx
import pytest

from lettr._exceptions import (
    ConflictError,
    IdempotencyConflictError,
    IdempotencyInProgressError,
    ValidationError,
    raise_for_status,
)
from lettr._idempotency import is_valid_idempotency_key, validate_idempotency_key
from lettr.resources.emails import Emails

ACCEPTED = {"data": {"request_id": "req-1", "accepted": 1, "rejected": 0}}


def send(client, **kwargs):
    return Emails(client).send(
        from_email="sender@example.com",
        to=["recipient@example.com"],
        subject="Hello",
        html="<p>Hi</p>",
        **kwargs,
    )


class TestKeyValidation:
    @pytest.mark.parametrize(
        "key",
        ["order-confirmation-12345", "a.b_c-1", "a", "a" * 255],
    )
    def test_accepts_the_documented_format(self, key: str) -> None:
        assert is_valid_idempotency_key(key)

    @pytest.mark.parametrize(
        "key",
        ["", "order 123", "order/123", "order:123", "order-č", "a" * 256],
    )
    def test_rejects_anything_else(self, key: str) -> None:
        assert not is_valid_idempotency_key(key)

        with pytest.raises(ValidationError):
            validate_idempotency_key(key)

    def test_a_bad_key_never_reaches_the_api(self, mock_client) -> None:
        """Validated locally, so it costs no round trip and no 422."""
        with pytest.raises(ValidationError):
            send(mock_client, idempotency_key="order 123")

        mock_client.post.assert_not_called()
        mock_client.post_with_headers.assert_not_called()


class TestSendingTheKey:
    def test_puts_the_key_in_the_header_not_the_body(self, mock_client) -> None:
        mock_client.post_with_headers.return_value = (ACCEPTED, httpx.Headers({}))

        send(mock_client, idempotency_key="order-12345")

        _, kwargs = mock_client.post_with_headers.call_args
        assert kwargs["headers"] == {"Idempotency-Key": "order-12345"}
        assert "idempotency_key" not in kwargs["json"]

    def test_no_key_means_no_header(self, mock_client) -> None:
        """The compatibility guarantee: an existing caller's request is unchanged."""
        mock_client.post.return_value = ACCEPTED

        result = send(mock_client)

        mock_client.post.assert_called_once()
        mock_client.post_with_headers.assert_not_called()
        # Nothing to replay without a key, so it is definitionally False.
        assert result.replayed is False


class TestReadingTheAnswer:
    def test_a_replay_is_a_success_that_says_so(self, mock_client) -> None:
        mock_client.post_with_headers.return_value = (
            ACCEPTED,
            httpx.Headers({"Idempotency-Replayed": "true"}),
        )

        result = send(mock_client, idempotency_key="order-12345")

        # No second email went out, but nothing failed either.
        assert result.replayed is True
        assert result.accepted == 1

    def test_reads_the_header_case_insensitively(self, mock_client) -> None:
        mock_client.post_with_headers.return_value = (
            ACCEPTED,
            httpx.Headers({"idempotency-replayed": "TRUE"}),
        )

        assert send(mock_client, idempotency_key="order-12345").replayed is True

    def test_a_normal_send_is_not_replayed(self, mock_client) -> None:
        mock_client.post_with_headers.return_value = (ACCEPTED, httpx.Headers({}))

        assert send(mock_client, idempotency_key="order-12345").replayed is False


class TestTheTwoConflicts:
    """One is safe to retry with the same key; the other fails forever."""

    def test_in_progress_is_retryable_and_carries_retry_after(self) -> None:
        with pytest.raises(IdempotencyInProgressError) as exc:
            raise_for_status(
                409,
                {
                    "message": "A request with this Idempotency-Key is still processing.",
                    "error_code": "idempotency_in_progress",
                },
                httpx.Headers({"Retry-After": "3"}),
            )

        assert exc.value.retry_after == 3
        assert isinstance(exc.value, ConflictError)

    def test_in_progress_without_retry_after(self) -> None:
        with pytest.raises(IdempotencyInProgressError) as exc:
            raise_for_status(
                409,
                {"message": "still processing", "error_code": "idempotency_in_progress"},
                httpx.Headers({}),
            )

        assert exc.value.retry_after is None

    def test_a_payload_conflict_must_not_be_retried(self) -> None:
        with pytest.raises(IdempotencyConflictError) as exc:
            raise_for_status(
                409,
                {
                    "message": (
                        "This Idempotency-Key was already used with a different request payload."
                    ),
                    "error_code": "idempotency_key_conflict",
                },
                httpx.Headers({}),
            )

        assert isinstance(exc.value, ConflictError)
        assert not hasattr(exc.value, "retry_after")

    def test_an_unrelated_409_stays_a_plain_conflict(self) -> None:
        with pytest.raises(ConflictError) as exc:
            raise_for_status(
                409,
                {
                    "message": "A contact with this email already exists.",
                    "error_code": "resource_already_exists",
                },
                httpx.Headers({}),
            )

        assert not isinstance(exc.value, IdempotencyConflictError)
        assert not isinstance(exc.value, IdempotencyInProgressError)

    def test_raise_for_status_still_works_without_headers(self) -> None:
        """The headers argument is optional, so existing callers are unaffected."""
        with pytest.raises(IdempotencyInProgressError) as exc:
            raise_for_status(
                409,
                {"message": "still processing", "error_code": "idempotency_in_progress"},
            )

        assert exc.value.retry_after is None
