"""Webhook management."""

from __future__ import annotations

from typing import List

from .._client import ApiClient
from .._types import Webhook


class Webhooks:
    """Operations for retrieving webhooks.

    Usage::

        webhooks = client.webhooks.list()
        webhook = client.webhooks.get("webhook-abc123")
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(self) -> List[Webhook]:
        """List all webhooks.

        Returns:
            A list of :class:`Webhook` objects.
        """
        body = self._client.get("/webhooks")
        return [
            Webhook(
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
            for w in body["data"]["webhooks"]
        ]

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
        w = body["data"]
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
