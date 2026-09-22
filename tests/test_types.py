"""Tests for type definitions."""

from __future__ import annotations

from lettr._types import (
    EmailOptions,
    GeoIp,
    ScheduledEmail,
    ScheduledEmailPage,
    UserAgentParsed,
)


class TestEmailOptions:
    def test_to_dict_filters_none(self) -> None:
        opts = EmailOptions(click_tracking=True, open_tracking=None, transactional=False)
        result = opts.to_dict()
        assert result == {"click_tracking": True, "transactional": False}

    def test_to_dict_empty(self) -> None:
        opts = EmailOptions()
        assert opts.to_dict() == {}

    def test_to_dict_all_set(self) -> None:
        opts = EmailOptions(
            click_tracking=True,
            open_tracking=False,
            transactional=True,
            inline_css=False,
            perform_substitutions=True,
        )
        result = opts.to_dict()
        assert len(result) == 5
        assert result["perform_substitutions"] is True


class TestGeoIp:
    def test_all_optional(self) -> None:
        geo = GeoIp()
        assert geo.country is None
        assert geo.latitude is None

    def test_with_values(self) -> None:
        geo = GeoIp(country="US", latitude=37.77, longitude=-122.42)
        assert geo.country == "US"
        assert geo.latitude == 37.77


class TestUserAgentParsed:
    def test_all_optional(self) -> None:
        ua = UserAgentParsed()
        assert ua.agent_family is None
        assert ua.is_mobile is None

    def test_with_values(self) -> None:
        ua = UserAgentParsed(agent_family="Chrome", is_mobile=True)
        assert ua.agent_family == "Chrome"
        assert ua.is_mobile is True


class TestScheduledEmail:
    def test_creation(self) -> None:
        se = ScheduledEmail(
            transmission_id=None,
            state="scheduled",
            from_email="sender@example.com",
            subject="Hello",
            recipients=["a@b.com"],
            num_recipients=1,
            events=[],
            scheduled_at="2026-12-01T10:00:00Z",
            request_id="sch_01M322YMWVCZ4RNYXHMSSMDTM1",
            accepted=1,
        )
        assert se.request_id == "sch_01M322YMWVCZ4RNYXHMSSMDTM1"
        assert se.transmission_id is None
        assert se.state == "scheduled"
        assert se.from_email == "sender@example.com"
        assert se.num_recipients == 1
        assert se.accepted == 1
        assert se.events == []
        assert se.from_name is None

    def test_new_fields_default(self) -> None:
        """A 1.6.0-shaped constructor call still works, unchanged."""
        se = ScheduledEmail(
            transmission_id="7628974099477333734",
            state="delivered",
            from_email="sender@example.com",
            subject="Hello",
            recipients=["a@b.com"],
            num_recipients=1,
            events=[],
        )
        assert se.request_id == ""
        assert se.accepted == 0
        assert se.rejected == 0
        assert se.tag is None
        assert se.failure_reason is None


class TestScheduledEmailPage:
    def test_creation(self) -> None:
        page = ScheduledEmailPage(
            scheduled_emails=[],
            total=0,
            per_page=25,
            current_page=1,
            last_page=0,
        )
        assert page.scheduled_emails == []
        assert page.per_page == 25
