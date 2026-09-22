"""Tests for the Emails resource."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from lettr._types import (
    Attachment,
    EmailDetail,
    EmailEventList,
    EmailList,
    EmailOptions,
    ScheduledEmail,
    ScheduledEmailPage,
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


def _scheduled(**overrides: object) -> dict:
    """Build one scheduled email as the API returns it now."""
    base = {
        "request_id": "sch_01M322YMWVCZ4RNYXHMSSMDTM1",
        "transmission_id": None,
        "state": "scheduled",
        "scheduled_at": "2026-09-21T15:37:10Z",
        "from": "sender@example.com",
        "from_name": None,
        "subject": "Scheduled Newsletter",
        "recipients": ["recipient@example.com"],
        "num_recipients": 1,
        "accepted": 1,
        "rejected": 0,
        "tag": None,
        "failure_reason": None,
        "events": [],
    }
    base.update(overrides)
    return base


class TestSchedule:
    def test_schedule_email(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "message": "Email scheduled for delivery.",
            "data": _scheduled(subject="Later", tag="scheduled-test"),
        }

        result = emails.schedule(
            from_email="a@b.com",
            to=["c@d.com"],
            subject="Later",
            html="<p>Hi</p>",
            scheduled_at="2026-12-01T10:00:00Z",
            tag="scheduled-test",
        )

        assert isinstance(result, ScheduledEmail)
        assert result.request_id == "sch_01M322YMWVCZ4RNYXHMSSMDTM1"
        assert result.transmission_id is None
        assert result.state == "scheduled"
        assert result.accepted == 1
        assert result.rejected == 0
        assert result.tag == "scheduled-test"

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["scheduled_at"] == "2026-12-01T10:00:00Z"
        assert payload["tag"] == "scheduled-test"
        mock_client.post.assert_called_once()
        assert mock_client.post.call_args.args[0] == "/emails/scheduled"

    def test_schedule_accepts_datetime(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": _scheduled()}

        emails.schedule(
            from_email="a@b.com",
            to=["c@d.com"],
            subject="Later",
            html="<p>Hi</p>",
            scheduled_at=datetime(2026, 12, 1, 10, 0, tzinfo=timezone.utc),
        )

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["scheduled_at"] == "2026-12-01T10:00:00+00:00"


class TestGetScheduled:
    def test_get_scheduled(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "message": "Scheduled transmission retrieved successfully.",
            "data": _scheduled(from_name="Sender"),
        }

        result = emails.get_scheduled("sch_01M322YMWVCZ4RNYXHMSSMDTM1")
        assert isinstance(result, ScheduledEmail)
        assert result.request_id == "sch_01M322YMWVCZ4RNYXHMSSMDTM1"
        assert result.state == "scheduled"
        assert result.from_email == "sender@example.com"
        assert result.from_name == "Sender"
        assert result.subject == "Scheduled Newsletter"
        assert result.recipients == ["recipient@example.com"]
        assert result.num_recipients == 1
        assert result.events == []
        mock_client.get.assert_called_once_with("/emails/scheduled/sch_01M322YMWVCZ4RNYXHMSSMDTM1")

    def test_transmission_id_is_none_until_sent(
        self, emails: Emails, mock_client: MagicMock
    ) -> None:
        """The provider id webhooks carry does not exist yet while queued."""
        mock_client.get.return_value = {"data": _scheduled()}

        result = emails.get_scheduled("sch_01M322YMWVCZ4RNYXHMSSMDTM1")
        assert result.transmission_id is None
        assert result.request_id == "sch_01M322YMWVCZ4RNYXHMSSMDTM1"

    def test_transmission_id_present_once_sent(
        self, emails: Emails, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {
            "data": _scheduled(state="sent", transmission_id="7628974099477333734")
        }

        result = emails.get_scheduled("sch_01M322YMWVCZ4RNYXHMSSMDTM1")
        assert result.state == "sent"
        assert result.transmission_id == "7628974099477333734"
        assert result.request_id == "sch_01M322YMWVCZ4RNYXHMSSMDTM1"

    @pytest.mark.parametrize("state", ["scheduled", "sending", "sent", "cancelled", "failed"])
    def test_every_state_parses(self, emails: Emails, mock_client: MagicMock, state: str) -> None:
        mock_client.get.return_value = {"data": _scheduled(state=state)}

        assert emails.get_scheduled("sch_1").state == state

    def test_failure_reason(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": _scheduled(
                state="failed", accepted=0, rejected=1, failure_reason="Sending domain removed."
            )
        }

        result = emails.get_scheduled("sch_1")
        assert result.failure_reason == "Sending domain removed."
        assert result.rejected == 1

    def test_get_scheduled_legacy_shape(self, emails: Emails, mock_client: MagicMock) -> None:
        """A pre-rework transmission id is answered from delivery events.

        That payload predates Lettr owning the schedule, so it has no
        ``request_id`` and none of the fields Lettr's own record carries.
        Parsing must not blow up, and ``request_id`` has to fall back to the
        id the caller actually asked about.
        """
        mock_client.get.return_value = {
            "data": {
                "transmission_id": "7628974099477333734",
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

        result = emails.get_scheduled("7628974099477333734")
        assert result.request_id == "7628974099477333734"
        assert result.transmission_id == "7628974099477333734"
        assert result.accepted == 0
        assert result.rejected == 0
        assert result.tag is None
        assert result.failure_reason is None
        assert len(result.events) == 1
        assert result.events[0].type == "delivery"
        assert result.events[0].rcpt_to == "recipient@example.com"


class TestListScheduled:
    def test_list_scheduled(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "message": "Scheduled emails retrieved successfully.",
            "data": {
                "scheduled_emails": [
                    _scheduled(),
                    _scheduled(request_id="sch_2", state="cancelled", accepted=0),
                ],
                "pagination": {
                    "total": 2,
                    "per_page": 2,
                    "current_page": 1,
                    "last_page": 1,
                },
            },
        }

        result = emails.list_scheduled()
        assert isinstance(result, ScheduledEmailPage)
        assert len(result.scheduled_emails) == 2
        assert result.scheduled_emails[0].state == "scheduled"
        assert result.scheduled_emails[1].request_id == "sch_2"
        assert result.scheduled_emails[1].state == "cancelled"
        assert result.total == 2
        assert result.per_page == 2
        assert result.current_page == 1
        assert result.last_page == 1
        assert mock_client.get.call_args.args[0] == "/emails/scheduled"
        assert mock_client.get.call_args.kwargs["params"] == {}

    def test_list_scheduled_with_filters(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "scheduled_emails": [],
                "pagination": {
                    "total": 0,
                    "per_page": 10,
                    "current_page": 2,
                    "last_page": 0,
                },
            }
        }

        result = emails.list_scheduled(status="cancelled", per_page=10, page=2)
        assert result.scheduled_emails == []

        params = mock_client.get.call_args.kwargs["params"]
        assert params == {"status": "cancelled", "per_page": 10, "page": 2}


class TestCancelScheduled:
    def test_cancel_scheduled(self, emails: Emails, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {
            "message": "Scheduled transmission cancelled successfully.",
            "data": _scheduled(state="cancelled", accepted=0),
        }

        result = emails.cancel_scheduled("sch_01M322YMWVCZ4RNYXHMSSMDTM1")
        assert isinstance(result, ScheduledEmail)
        assert result.state == "cancelled"
        assert result.accepted == 0
        assert result.request_id == "sch_01M322YMWVCZ4RNYXHMSSMDTM1"
        mock_client.delete.assert_called_once_with(
            "/emails/scheduled/sch_01M322YMWVCZ4RNYXHMSSMDTM1"
        )
