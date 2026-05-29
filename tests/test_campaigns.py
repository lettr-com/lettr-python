"""Tests for the Campaigns resource."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from lettr._types import (
    Campaign,
    CampaignDetail,
    CampaignEventPage,
    CampaignPage,
    CampaignStats,
)
from lettr.resources.campaigns import Campaigns

# ---------------------------------------------------------------------------
# Fixtures & data
# ---------------------------------------------------------------------------


@pytest.fixture()
def campaigns(mock_client: MagicMock) -> Campaigns:
    return Campaigns(mock_client)


STATS_DATA = {
    "injections": 100,
    "deliveries": 98,
    "bounces": 2,
    "spam_complaints": 1,
    "opens": 60,
    "unique_opens": 45,
    "clicks": 20,
    "unique_clicks": 15,
    "unsubscribes": 3,
}

CAMPAIGN_DATA = {
    "id": "camp_1",
    "name": "Spring Sale",
    "status": "sent",
    "sent_count": 124,
    "created_at": "2026-05-01T09:00:00+00:00",
    "stats": STATS_DATA,
    "subject": "Big news",
    "from_email": "hi@example.com",
    "from_name": "Example",
    "reply_to": "reply@example.com",
    "scheduled_at": None,
    "total_recipients": 124,
    "sent_at": "2026-05-01T10:00:00+00:00",
}

# Detail payload (what `get` returns) — same as CAMPAIGN_DATA plus html_content.
CAMPAIGN_DETAIL_DATA = {**CAMPAIGN_DATA, "html_content": "<h1>Hi</h1>"}

# Minimal payload — only the 6 OpenAPI-required fields; every nullable key
# absent. Exercises `_parse_campaign`'s `.get()` defaults so a refactor that
# regresses to `d["subject"]` would fail loudly here.
MINIMAL_CAMPAIGN_DATA = {
    "id": "camp_min",
    "name": "Draft",
    "status": "draft",
    "sent_count": 0,
    "created_at": "2026-05-01T09:00:00+00:00",
    "stats": STATS_DATA,
}

EVENT_DATA = {
    "event_id": "92356829",
    "event_type": "open",
    "email": "jane@example.com",
    "timestamp": "2026-05-01T12:30:00+00:00",
    "bounce_class": None,
    "reason": None,
    "target_link_url": None,
    "user_agent": "Mozilla/5.0",
}

PAGINATION = {"total": 1, "per_page": 20, "current_page": 1, "last_page": 1}


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    def test_list(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {"campaigns": [CAMPAIGN_DATA], "pagination": PAGINATION}
        }
        page = campaigns.list()
        assert isinstance(page, CampaignPage)
        assert len(page.campaigns) == 1
        assert page.campaigns[0].name == "Spring Sale"
        assert isinstance(page.campaigns[0].stats, CampaignStats)
        assert page.campaigns[0].stats.unique_opens == 45
        # list responses return the base type, not the detail variant
        assert type(page.campaigns[0]) is Campaign
        assert page.total == 1
        assert page.per_page == 20
        mock_client.get.assert_called_once_with("/campaigns", params={})

    def test_list_forwards_filters(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"campaigns": [], "pagination": PAGINATION}}
        campaigns.list(page=2, per_page=50, status="sent")
        params = mock_client.get.call_args.kwargs["params"]
        assert params == {"page": 2, "per_page": 50, "status": "sent"}

    def test_list_handles_minimal_payload(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        # Every nullable key absent — exercises the `.get()` defaults in the parser
        # so a refactor to `d["subject"]` would crash with KeyError.
        mock_client.get.return_value = {
            "data": {"campaigns": [MINIMAL_CAMPAIGN_DATA], "pagination": PAGINATION}
        }
        page = campaigns.list()
        c = page.campaigns[0]
        assert c.id == "camp_min"
        assert c.subject is None
        assert c.from_email is None
        assert c.from_name is None
        assert c.reply_to is None
        assert c.scheduled_at is None
        assert c.total_recipients is None
        assert c.sent_at is None

    def test_list_drops_unexpected_html_content(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        # Regression guard: even if the API ever leaks html_content into
        # a list item, _from_dict's field-set filter must strip it before
        # construction so the base Campaign instance has no such attribute.
        polluted = {**CAMPAIGN_DATA, "html_content": "<h1>leak</h1>"}
        mock_client.get.return_value = {"data": {"campaigns": [polluted], "pagination": PAGINATION}}
        page = campaigns.list()
        assert not hasattr(page.campaigns[0], "html_content")


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestGet:
    def test_get(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": CAMPAIGN_DETAIL_DATA}
        result = campaigns.get("camp_1")
        # CampaignDetail IS-A Campaign — substitutability preserved for
        # existing summary-shaped callers.
        assert isinstance(result, CampaignDetail)
        assert result.id == "camp_1"
        assert result.html_content == "<h1>Hi</h1>"
        assert result.stats.clicks == 20
        mock_client.get.assert_called_once_with("/campaigns/camp_1")


# ---------------------------------------------------------------------------
# list_events
# ---------------------------------------------------------------------------


class TestListEvents:
    def test_list_events(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"events": [EVENT_DATA], "next_cursor": "abc123"}}
        page = campaigns.list_events("camp_1")
        assert isinstance(page, CampaignEventPage)
        assert len(page.events) == 1
        assert page.events[0].event_type == "open"
        assert page.events[0].user_agent == "Mozilla/5.0"
        assert page.next_cursor == "abc123"
        mock_client.get.assert_called_once_with("/campaigns/camp_1/events", params={})

    def test_list_events_forwards_filters(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"data": {"events": [], "next_cursor": None}}
        campaigns.list_events(
            "camp_1",
            event_type="click",
            email="jane@example.com",
            start_date="2026-05-01T00:00:00Z",
            end_date="2026-05-31T00:00:00Z",
            limit=50,
            cursor="cur_1",
        )
        params = mock_client.get.call_args.kwargs["params"]
        assert params == {
            "event_type": "click",
            "email": "jane@example.com",
            "start_date": "2026-05-01T00:00:00Z",
            "end_date": "2026-05-31T00:00:00Z",
            "limit": 50,
            "cursor": "cur_1",
        }

    def test_list_events_null_cursor(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"events": [], "next_cursor": None}}
        page = campaigns.list_events("camp_1")
        assert page.next_cursor is None


# ---------------------------------------------------------------------------
# send / schedule / unschedule
# ---------------------------------------------------------------------------


class TestSend:
    def test_send_returns_campaign(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"message": "Sending.", "data": CAMPAIGN_DATA}
        result = campaigns.send("camp_1")
        # Action endpoints return the base Campaign, never the detail variant.
        assert type(result) is Campaign
        assert result.id == "camp_1"
        mock_client.post.assert_called_once_with("/campaigns/camp_1/send")

    def test_send_without_data_returns_none(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"message": "Sending."}
        assert campaigns.send("camp_1") is None


class TestSchedule:
    def test_schedule_returns_campaign(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        scheduled = {**CAMPAIGN_DATA, "status": "scheduled"}
        mock_client.post.return_value = {"message": "Scheduled.", "data": scheduled}
        result = campaigns.schedule("camp_1", scheduled_at="2026-06-01T09:00:00+00:00")
        assert type(result) is Campaign
        assert result.status == "scheduled"
        mock_client.post.assert_called_once_with(
            "/campaigns/camp_1/schedule",
            json={"scheduled_at": "2026-06-01T09:00:00+00:00"},
        )

    def test_schedule_accepts_datetime(self, campaigns: Campaigns, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"message": "Scheduled.", "data": CAMPAIGN_DATA}
        dt = datetime(2026, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
        campaigns.schedule("camp_1", scheduled_at=dt)
        mock_client.post.assert_called_once_with(
            "/campaigns/camp_1/schedule",
            json={"scheduled_at": dt.isoformat()},
        )

    def test_schedule_without_data_returns_none(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"message": "Scheduled."}
        assert campaigns.schedule("camp_1", scheduled_at="2026-06-01T09:00:00+00:00") is None


class TestUnschedule:
    def test_unschedule_returns_campaign(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        drafted = {**CAMPAIGN_DATA, "status": "draft"}
        mock_client.post.return_value = {"message": "Unscheduled.", "data": drafted}
        result = campaigns.unschedule("camp_1")
        assert type(result) is Campaign
        assert result.status == "draft"
        mock_client.post.assert_called_once_with("/campaigns/camp_1/unschedule")

    def test_unschedule_without_data_returns_none(
        self, campaigns: Campaigns, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"message": "Unscheduled."}
        assert campaigns.unschedule("camp_1") is None
