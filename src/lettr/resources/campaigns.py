"""Campaign management — list, inspect, and send/schedule campaigns."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .._client import ApiClient
from .._types import (
    Campaign,
    CampaignEvent,
    CampaignEventPage,
    CampaignPage,
    CampaignStats,
    _from_dict,
    _pagination_kwargs,
)

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def _parse_campaign(d: dict[str, Any]) -> Campaign:
    """Parse a campaign payload (CampaignSummary or CampaignDetail).

    The ``html_content`` field is only present on the detail (``get``)
    response; for list responses it stays ``None``. Unknown keys are
    silently dropped via :func:`_from_dict` so the parser is
    forward-compatible.
    """
    return _from_dict(
        Campaign,
        {**d, "stats": _from_dict(CampaignStats, d["stats"])},
    )


def _parse_event(d: dict[str, Any]) -> CampaignEvent:
    return _from_dict(CampaignEvent, d)


def _parse_action_response(body: dict[str, Any]) -> Campaign | None:
    """Parse the optional ``data`` campaign from an action response.

    The ``CampaignActionResponse`` schema makes ``data`` optional — the
    server omits it in the rare case the campaign can't be re-read after
    the action (e.g. it was concurrently deleted). ``None`` here means
    "absent key", not "empty object": a spec-violating ``data: {}`` is
    intentionally left to raise inside :func:`_parse_campaign` rather than
    being silently swallowed.
    """
    data = body.get("data")
    return _parse_campaign(data) if data is not None else None


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------


class Campaigns:
    """Operations for campaigns.

    Campaigns are read-only over the API (no create/update/delete); they are
    authored in the Lettr app. This resource lists them, reads a single
    campaign, inspects engagement events, and triggers delivery.

    Usage::

        page = client.campaigns.list(status="sent")
        campaign = client.campaigns.get(page.campaigns[0].id)
        events = client.campaigns.list_events(campaign.id, event_type="open")
        client.campaigns.schedule(campaign.id, scheduled_at="2026-06-01T09:00:00+00:00")
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        page: int | None = None,
        per_page: int | None = None,
        status: str | None = None,
    ) -> CampaignPage:
        """List campaigns with pagination.

        Args:
            page: Page number (1-based).
            per_page: Results per page (1-100, default 20).
            status: Filter by status — one of ``draft``, ``scheduled``,
                ``preparing``, ``in_review``, ``sending``, ``sent``, ``failed``.

        Returns:
            A :class:`CampaignPage` with campaigns and pagination info.
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        if status is not None:
            params["status"] = status

        body = self._client.get("/campaigns", params=params)
        data = body["data"]
        return CampaignPage(
            campaigns=[_parse_campaign(item) for item in data["campaigns"]],
            **_pagination_kwargs(data["pagination"]),
        )

    def get(self, campaign_id: str) -> Campaign:
        """Get a single campaign by ID, including its rendered HTML content.

        The returned :class:`Campaign` has ``html_content`` populated; list
        responses leave it as ``None``.
        """
        body = self._client.get(f"/campaigns/{campaign_id}")
        return _parse_campaign(body["data"])

    def list_events(
        self,
        campaign_id: str,
        *,
        event_type: str | None = None,
        email: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> CampaignEventPage:
        """List engagement events for a campaign with cursor-based pagination.

        Args:
            campaign_id: The campaign ID.
            event_type: Filter by event type — one of ``injection``,
                ``delivery``, ``bounce``, ``spam_complaint``, ``open``,
                ``click``, ``list_unsubscribe``.
            email: Filter by recipient email address.
            start_date: Only events on or after this time (ISO 8601).
            end_date: Only events on or before this time (ISO 8601).
            limit: Results per page (1-100, default 25).
            cursor: Pagination cursor from a previous response.

        Returns:
            A :class:`CampaignEventPage` with events and the next cursor.
        """
        params: dict[str, Any] = {}
        if event_type is not None:
            params["event_type"] = event_type
        if email is not None:
            params["email"] = email
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        body = self._client.get(f"/campaigns/{campaign_id}/events", params=params)
        data = body["data"]
        # next_cursor is `required` in the OpenAPI schema (nullable but
        # always present), so use [] — a missing key here is a server
        # regression we want to surface, not silently treat as end-of-pages.
        return CampaignEventPage(
            events=[_parse_event(item) for item in data["events"]],
            next_cursor=data["next_cursor"],
        )

    def send(self, campaign_id: str) -> Campaign | None:
        """Send a campaign immediately.

        Returns:
            The updated :class:`Campaign`, or ``None`` if the API does not
            return the campaign (e.g. it was concurrently deleted).
        """
        body = self._client.post(f"/campaigns/{campaign_id}/send")
        return _parse_action_response(body)

    def schedule(
        self,
        campaign_id: str,
        *,
        scheduled_at: datetime | str,
    ) -> Campaign | None:
        """Schedule a campaign for future delivery.

        Args:
            campaign_id: The campaign ID.
            scheduled_at: Future delivery time. Accepts either an ISO 8601
                string or a :class:`~datetime.datetime` (which is rendered
                via ``.isoformat()``). Include a timezone offset
                (e.g. ``+02:00`` or ``Z``); naive values are interpreted as
                UTC. Must be in the future.

        Returns:
            The updated :class:`Campaign`, or ``None`` if the API does not
            return the campaign.
        """
        scheduled_at_str = (
            scheduled_at.isoformat() if isinstance(scheduled_at, datetime) else scheduled_at
        )
        body = self._client.post(
            f"/campaigns/{campaign_id}/schedule",
            json={"scheduled_at": scheduled_at_str},
        )
        return _parse_action_response(body)

    def unschedule(self, campaign_id: str) -> Campaign | None:
        """Cancel a campaign's scheduled delivery, returning it to draft.

        Returns:
            The updated :class:`Campaign`, or ``None`` if the API does not
            return the campaign.
        """
        body = self._client.post(f"/campaigns/{campaign_id}/unschedule")
        return _parse_action_response(body)
