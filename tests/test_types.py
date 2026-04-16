"""Tests for type definitions."""

from __future__ import annotations

from lettr._types import EmailOptions, GeoIp, ScheduledEmail, UserAgentParsed


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
            transmission_id="tr_123",
            state="submitted",
            from_email="sender@example.com",
            subject="Hello",
            recipients=["a@b.com"],
            num_recipients=1,
            events=[],
            scheduled_at="2025-12-01T10:00:00Z",
        )
        assert se.transmission_id == "tr_123"
        assert se.state == "submitted"
        assert se.from_email == "sender@example.com"
        assert se.num_recipients == 1
        assert se.events == []
        assert se.from_name is None
