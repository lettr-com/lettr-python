"""Webhook management."""

from __future__ import annotations

import builtins
from typing import Any

from .._client import ApiClient
from .._types import Webhook


def _parse_webhook(w: dict[str, Any]) -> Webhook:
    """Parse a raw dict into a Webhook."""
    return Webhook(
        id=w["id"],
        name=w["name"],
        url=w["url"],
        enabled=w["enabled"],
        auth_type=w["auth_type"],
        has_auth_credentials=w["has_auth_credentials"],
        event_types=w.get("event_types"),
        last_successful_at=w.get("last_successful_at"),
        last_failure_at=w.get("last_failure_at"),
        last_status=w.get("last_status"),
    )


class Webhooks:
    """Operations for managing webhooks.

    Usage::

        webhooks = client.webhooks.list()
        webhook = client.webhooks.get("webhook-abc123")
        webhook = client.webhooks.create(
            name="My Webhook",
            url="https://example.com/webhook",
            auth_type="none",
            events_mode="all",
        )
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(self) -> builtins.list[Webhook]:
        """List all webhooks.

        Returns:
            A list of :class:`Webhook` objects.
        """
        body = self._client.get("/webhooks")
        return [_parse_webhook(w) for w in body["data"]["webhooks"]]

    def get(self, webhook_id: str) -> Webhook:
        """Get details of a single webhook.

        Args:
            webhook_id: The webhook ID.

        Returns:
            A :class:`Webhook` with full details.

        Raises:
            NotFoundError: If the webhook is not found.
        """
        body = self._client.get(f"/webhooks/{webhook_id}")
        return _parse_webhook(body["data"])

    def create(
        self,
        *,
        name: str,
        url: str,
        auth_type: str,
        events_mode: str,
        auth_username: str | None = None,
        auth_password: str | None = None,
        oauth_client_id: str | None = None,
        oauth_client_secret: str | None = None,
        oauth_token_url: str | None = None,
        events: builtins.list[str] | None = None,
    ) -> Webhook:
        """Create a new webhook.

        Args:
            name: Webhook name.
            url: Webhook URL to receive events.
            auth_type: Authentication type (``"none"``, ``"basic"``, ``"oauth2"``).
            events_mode: Event mode (``"all"`` or ``"selected"``).
            auth_username: Basic auth username (when ``auth_type="basic"``).
            auth_password: Basic auth password (when ``auth_type="basic"``).
            oauth_client_id: OAuth2 client ID (when ``auth_type="oauth2"``).
            oauth_client_secret: OAuth2 client secret (when ``auth_type="oauth2"``).
            oauth_token_url: OAuth2 token URL (when ``auth_type="oauth2"``).
            events: Event types to receive (when ``events_mode="selected"``).

        Returns:
            A :class:`Webhook` with the created webhook details.

        Raises:
            ValidationError: If validation fails.
            ConflictError: If a webhook with the same URL already exists.
        """
        payload: dict[str, Any] = {
            "name": name,
            "url": url,
            "auth_type": auth_type,
            "events_mode": events_mode,
        }
        if auth_username is not None:
            payload["auth_username"] = auth_username
        if auth_password is not None:
            payload["auth_password"] = auth_password
        if oauth_client_id is not None:
            payload["oauth_client_id"] = oauth_client_id
        if oauth_client_secret is not None:
            payload["oauth_client_secret"] = oauth_client_secret
        if oauth_token_url is not None:
            payload["oauth_token_url"] = oauth_token_url
        if events is not None:
            payload["events"] = events

        body = self._client.post("/webhooks", json=payload)
        return _parse_webhook(body["data"])

    def update(
        self,
        webhook_id: str,
        *,
        name: str | None = None,
        target: str | None = None,
        auth_type: str | None = None,
        auth_username: str | None = None,
        auth_password: str | None = None,
        oauth_token_url: str | None = None,
        oauth_client_id: str | None = None,
        oauth_client_secret: str | None = None,
        events: builtins.list[str] | None = None,
        active: bool | None = None,
    ) -> Webhook:
        """Update an existing webhook.

        Only provided fields will be updated.

        Args:
            webhook_id: The webhook ID to update.
            name: New webhook name.
            target: New webhook URL.
            auth_type: New authentication type.
            auth_username: New basic auth username.
            auth_password: New basic auth password.
            oauth_token_url: New OAuth2 token URL.
            oauth_client_id: New OAuth2 client ID.
            oauth_client_secret: New OAuth2 client secret.
            events: New event types to receive.
            active: Enable or disable the webhook.

        Returns:
            A :class:`Webhook` with the updated webhook details.

        Raises:
            NotFoundError: If the webhook is not found.
            ValidationError: If validation fails.
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if target is not None:
            payload["target"] = target
        if auth_type is not None:
            payload["auth_type"] = auth_type
        if auth_username is not None:
            payload["auth_username"] = auth_username
        if auth_password is not None:
            payload["auth_password"] = auth_password
        if oauth_token_url is not None:
            payload["oauth_token_url"] = oauth_token_url
        if oauth_client_id is not None:
            payload["oauth_client_id"] = oauth_client_id
        if oauth_client_secret is not None:
            payload["oauth_client_secret"] = oauth_client_secret
        if events is not None:
            payload["events"] = events
        if active is not None:
            payload["active"] = active

        body = self._client.put(f"/webhooks/{webhook_id}", json=payload)
        return _parse_webhook(body["data"])

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook.

        Args:
            webhook_id: The webhook ID to delete.

        Raises:
            NotFoundError: If the webhook is not found.
        """
        self._client.delete(f"/webhooks/{webhook_id}")
