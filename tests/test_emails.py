"""Tests for the Emails resource."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._types import (
    Attachment,
    EmailDetail,
    EmailEventList,
    EmailList,
    EmailOptions,
    ScheduledEmail,
    SendEmailResponse,
)
from lettr.resources.emails import Emails


@pytest.fixture()
def emails(mock_client: MagicMock) -> Emails:
    return Emails(mock_client)


class TestSend:
    def test_send_minimal(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {"request_id": "req_123", "accepted": 1, "rejected": 0}
        }

        result = emails.send(
            from_email="a@b.com",
            to=["c@d.com"],
            subject="Hi",
            html="<p>Hello</p>",
        )

        assert isinstance(result, SendEmailResponse)
        assert result.request_id == "req_123"
        assert result.accepted == 1

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["from"] == "a@b.com"
        assert payload["to"] == ["c@d.com"]
        assert payload["subject"] == "Hi"
        assert payload["html"] == "<p>Hello</p>"

    def test_send_with_all_options(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {"request_id": "req_456", "accepted": 2, "rejected": 0}
        }

        result = emails.send(
            from_email="a@b.com",
            to=["c@d.com", "e@f.com"],
            subject="Test",
            html="<p>Hi</p>",
            text="Hi",
            from_name="Sender",
            cc=["cc@test.com"],
            bcc=["bcc@test.com"],
            reply_to="reply@test.com",
            reply_to_name="Reply",
            amp_html="<p>AMP</p>",
            template_slug="welcome",
            template_version=2,
            project_id=10,
            tag="onboarding",
            metadata={"user_id": "123"},
            headers={"X-Custom": "value"},
            substitution_data={"name": "World"},
            options=EmailOptions(click_tracking=True, open_tracking=False),
            attachments=[Attachment(name="f.pdf", type="application/pdf", data="base64data")],
        )

        assert result.accepted == 2
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["tag"] == "onboarding"
        assert payload["headers"] == {"X-Custom": "value"}
        assert payload["cc"] == ["cc@test.com"]
        assert payload["options"] == {"click_tracking": True, "open_tracking": False}
        assert payload["attachments"] == [
            {"name": "f.pdf", "type": "application/pdf", "data": "base64data"}
        ]

    def test_send_without_subject(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {"request_id": "req_789", "accepted": 1, "rejected": 0}
        }

        emails.send(
            from_email="a@b.com",
            to=["c@d.com"],
            template_slug="welcome",
        )

        payload = mock_client.post.call_args.kwargs["json"]
        assert "subject" not in payload


class TestList:
    def test_list_default(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "events": {
                    "data": [
                        {
                            "event_id": "ev1",
                            "type": "injection",
                            "timestamp": "2025-01-01T00:00:00Z",
                            "request_id": "req_1",
                            "subject": "Hello",
                            "rcpt_to": "a@b.com",
                        }
                    ],
                    "total_count": 1,
                    "from": "2025-01-01T00:00:00Z",
                    "to": "2025-01-15T00:00:00Z",
                    "pagination": {"next_cursor": "abc", "per_page": 25},
                }
            }
        }

        result = emails.list()
        assert isinstance(result, EmailList)
        assert len(result.results) == 1
        assert result.total_count == 1
        assert result.next_cursor == "abc"
        assert result.date_from == "2025-01-01T00:00:00Z"
        assert result.date_to == "2025-01-15T00:00:00Z"
        assert result.results[0].type == "injection"

    def test_list_with_filters(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "events": {
                    "data": [],
                    "total_count": 0,
                    "from": None,
                    "to": None,
                    "pagination": {"per_page": 10},
                }
            }
        }

        emails.list(
            per_page=10,
            cursor="xyz",
            recipients="a@b.com",
            from_date="2025-01-01",
            to_date="2025-12-31",
        )

        params = mock_client.get.call_args.kwargs["params"]
        assert params["per_page"] == 10
        assert params["cursor"] == "xyz"
        assert params["recipients"] == "a@b.com"
        assert params["from"] == "2025-01-01"
        assert params["to"] == "2025-12-31"

    def test_list_regression_nested_events_wrapper(
        self, emails: Emails, mock_client: MagicMock
    ) -> None:
        """Regression: response uses data.events.data nesting per OpenAPI spec.

        Previously the SDK read from data.results and silently returned an
        empty list when the API actually had emails.
        """
        mock_client.get.return_value = {
            "success": True,
            "message": "Emails retrieved successfully.",
            "data": {
                "events": {
                    "data": [
                        {"event_id": "e1", "type": "delivery", "timestamp": "t1"},
                        {"event_id": "e2", "type": "delivery", "timestamp": "t2"},
                    ],
                    "total_count": 2,
                    "from": "2024-01-05T00:00:00Z",
                    "to": "2024-01-15T23:59:59Z",
                    "pagination": {"next_cursor": None, "per_page": 25},
                }
            },
        }

        result = emails.list()
        assert result.total_count == 2
        assert len(result.results) == 2


def _detail_envelope(**overrides: object) -> dict:
    """Build a spec-shaped detail response (`GET /emails/{id}`)."""
    base = {
        "transmission_id": "req_123",
        "state": "delivered",
        "from": "sender@example.com",
        "from_name": None,
        "subject": "Hello",
        "recipients": ["a@b.com"],
        "num_recipients": 1,
        "events": [],
    }
    base.update(overrides)
    return {"data": base}


class TestGet:
    def test_get_basic(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = _detail_envelope(
            events=[{"event_id": "ev1", "type": "delivery", "rcpt_to": "a@b.com"}]
        )

        result = emails.get("req_123")
        assert isinstance(result, EmailDetail)
        assert result.transmission_id == "req_123"
        assert result.state == "delivered"
        assert result.from_email == "sender@example.com"
        assert result.recipients == ["a@b.com"]
        assert result.num_recipients == 1
        assert len(result.events) == 1
        assert result.events[0].type == "delivery"

    def test_get_with_date_filters(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = _detail_envelope()

        emails.get("req_123", from_date="2025-01-01", to_date="2025-06-01")
        params = mock_client.get.call_args.kwargs["params"]
        assert params["from"] == "2025-01-01"
        assert params["to"] == "2025-06-01"

    def test_get_parses_nested_geo_ip(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = _detail_envelope(
            events=[
                {
                    "event_id": "ev1",
                    "type": "open",
                    "geo_ip": {
                        "country": "US",
                        "city": "San Francisco",
                        "latitude": 37.7749,
                        "longitude": -122.4194,
                    },
                    "user_agent_parsed": {
                        "agent_family": "Chrome",
                        "is_mobile": False,
                    },
                }
            ]
        )

        result = emails.get("req_123")
        event = result.events[0]
        assert event.geo_ip is not None
        assert event.geo_ip.country == "US"
        assert event.geo_ip.latitude == 37.7749
        assert event.user_agent_parsed is not None
        assert event.user_agent_parsed.agent_family == "Chrome"
        assert event.user_agent_parsed.is_mobile is False


class TestListEvents:
    def test_list_events_basic(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "events": {
                    "data": [
                        {"event_id": "ev1", "type": "delivery"},
                        {"event_id": "ev2", "type": "bounce"},
                    ],
                    "total_count": 2,
                    "from": "2025-01-01T00:00:00Z",
                    "to": "2025-01-15T00:00:00Z",
                    "pagination": {"next_cursor": None, "per_page": 25},
                }
            }
        }

        result = emails.list_events()
        assert isinstance(result, EmailEventList)
        assert len(result.results) == 2
        assert result.results[0].type == "delivery"
        assert result.date_from == "2025-01-01T00:00:00Z"

    def test_list_events_with_filters(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "events": {
                    "data": [],
                    "total_count": 0,
                    "from": None,
                    "to": None,
                    "pagination": {"per_page": 10},
                }
            }
        }

        emails.list_events(
            events=["delivery", "bounce"],
            recipients=["a@b.com"],
            from_date="2025-01-01",
            to_date="2025-12-31",
            per_page=10,
            cursor="abc",
            transmissions="tr_123",
            bounce_classes="10,30",
        )

        params = mock_client.get.call_args.kwargs["params"]
        assert params["events"] == "delivery,bounce"
        assert params["recipients"] == "a@b.com"
        assert params["from"] == "2025-01-01"
        assert params["transmissions"] == "tr_123"
        assert params["bounce_classes"] == "10,30"


class TestSchedule:
    def test_schedule_email(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "message": "Email scheduled for delivery.",
            "data": {
                "request_id": "12345678901234567890",
                "accepted": 1,
                "rejected": 0,
            },
        }

        result = emails.schedule(
            from_email="a@b.com",
            to=["c@d.com"],
            subject="Later",
            html="<p>Hi</p>",
            scheduled_at="2025-12-01T10:00:00Z",
            tag="scheduled-test",
        )

        assert isinstance(result, SendEmailResponse)
        assert result.request_id == "12345678901234567890"
        assert result.accepted == 1
        assert result.rejected == 0

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["scheduled_at"] == "2025-12-01T10:00:00Z"
        assert payload["tag"] == "scheduled-test"
        mock_client.post.assert_called_once()
        assert mock_client.post.call_args.args[0] == "/emails/scheduled"


class TestGetScheduled:
    def test_get_scheduled(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "message": "Scheduled transmission retrieved successfully.",
            "data": {
                "transmission_id": "tr_123",
                "state": "submitted",
                "scheduled_at": "2025-12-01T10:00:00Z",
                "from": "sender@example.com",
                "from_name": "Sender",
                "subject": "Scheduled Newsletter",
                "recipients": ["recipient@example.com"],
                "num_recipients": 1,
                "events": [],
            },
        }

        result = emails.get_scheduled("tr_123")
        assert isinstance(result, ScheduledEmail)
        assert result.transmission_id == "tr_123"
        assert result.state == "submitted"
        assert result.from_email == "sender@example.com"
        assert result.from_name == "Sender"
        assert result.subject == "Scheduled Newsletter"
        assert result.recipients == ["recipient@example.com"]
        assert result.num_recipients == 1
        assert result.events == []
        mock_client.get.assert_called_once_with("/emails/scheduled/tr_123")

    def test_get_scheduled_with_events(self, emails: Emails, mock_client: MagicMock) -> None:
        """Regression: events array contains EmailEvent objects, not strings."""
        mock_client.get.return_value = {
            "data": {
                "transmission_id": "tr_123",
                "state": "delivered",
                "scheduled_at": None,
                "from": "sender@example.com",
                "from_name": None,
                "subject": "Scheduled Newsletter",
                "recipients": ["recipient@example.com"],
                "num_recipients": 1,
                "events": [
                    {
                        "event_id": "evt-1",
                        "type": "delivery",
                        "timestamp": "2024-01-16T10:00:02.000Z",
                        "rcpt_to": "recipient@example.com",
                    }
                ],
            }
        }

        result = emails.get_scheduled("tr_123")
        assert len(result.events) == 1
        assert result.events[0].type == "delivery"
        assert result.events[0].rcpt_to == "recipient@example.com"


class TestCancelScheduled:
    def test_cancel_scheduled(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = None

        result = emails.cancel_scheduled("tr_123")
        assert result is None
        mock_client.delete.assert_called_once_with("/emails/scheduled/tr_123")
