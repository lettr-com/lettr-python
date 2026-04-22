"""Tests for the Webhooks resource."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._types import Webhook
from lettr.resources.webhooks import Webhooks


@pytest.fixture()
def webhooks(mock_client: MagicMock) -> Webhooks:
    return Webhooks(mock_client)


WEBHOOK_DATA = {
    "id": "wh_123",
    "name": "My Hook",
    "url": "https://example.com/hook",
    "enabled": True,
    "auth_type": "none",
    "has_auth_credentials": False,
    "event_types": ["message.delivery", "message.bounce"],
    "last_successful_at": "2025-06-01",
    "last_failure_at": None,
    "last_status": "200",
}


class TestList:
    def test_list_webhooks(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"webhooks": [WEBHOOK_DATA]}}

        result = webhooks.list()
        assert len(result) == 1
        assert isinstance(result[0], Webhook)
        assert result[0].id == "wh_123"
        assert result[0].event_types == ["message.delivery", "message.bounce"]


class TestGet:
    def test_get_webhook(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": WEBHOOK_DATA}

        result = webhooks.get("wh_123")
        assert isinstance(result, Webhook)
        assert result.name == "My Hook"
        mock_client.get.assert_called_once_with("/webhooks/wh_123")


class TestCreate:
    def test_create_webhook(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": WEBHOOK_DATA}

        result = webhooks.create(
            name="My Hook",
            url="https://example.com/hook",
            auth_type="none",
            events_mode="selected",
            events=["message.delivery", "message.bounce"],
        )

        assert isinstance(result, Webhook)
        assert result.id == "wh_123"

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["name"] == "My Hook"
        assert payload["auth_type"] == "none"
        assert payload["events_mode"] == "selected"
        assert payload["events"] == ["message.delivery", "message.bounce"]

    def test_create_with_basic_auth(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {**WEBHOOK_DATA, "auth_type": "basic", "has_auth_credentials": True}
        }

        webhooks.create(
            name="Secure Hook",
            url="https://example.com/hook",
            auth_type="basic",
            events_mode="all",
            auth_username="user",
            auth_password="pass",
        )

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["auth_username"] == "user"
        assert payload["auth_password"] == "pass"

    def test_create_with_oauth2(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {**WEBHOOK_DATA, "auth_type": "oauth2", "has_auth_credentials": True}
        }

        webhooks.create(
            name="OAuth Hook",
            url="https://example.com/hook",
            auth_type="oauth2",
            events_mode="all",
            oauth_client_id="cid",
            oauth_client_secret="csecret",
            oauth_token_url="https://auth.example.com/token",
        )

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["oauth_client_id"] == "cid"
        assert payload["oauth_client_secret"] == "csecret"
        assert payload["oauth_token_url"] == "https://auth.example.com/token"


class TestUpdate:
    def test_update_webhook(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"data": {**WEBHOOK_DATA, "name": "Renamed Hook"}}

        result = webhooks.update("wh_123", name="Renamed Hook", active=False)
        assert result.name == "Renamed Hook"

        payload = mock_client.put.call_args.kwargs["json"]
        assert payload == {"name": "Renamed Hook", "active": False}

    def test_update_partial(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"data": WEBHOOK_DATA}

        webhooks.update("wh_123", events=["message.delivery"])
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload == {"events": ["message.delivery"]}
        assert "name" not in payload

    def test_update_with_url(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {"data": WEBHOOK_DATA}

        webhooks.update("wh_123", url="https://new.example.com/hook")
        payload = mock_client.put.call_args.kwargs["json"]
        assert payload == {"url": "https://new.example.com/hook"}

    def test_update_target_deprecated(
        self, webhooks: Webhooks, mock_client: MagicMock
    ) -> None:
        mock_client.put.return_value = {"data": WEBHOOK_DATA}

        with pytest.warns(DeprecationWarning, match="target"):
            webhooks.update("wh_123", target="https://legacy.example.com/hook")

        payload = mock_client.put.call_args.kwargs["json"]
        assert payload == {"url": "https://legacy.example.com/hook"}

    def test_update_url_and_target_conflict(
        self, webhooks: Webhooks, mock_client: MagicMock
    ) -> None:
        with pytest.raises(TypeError, match="both"):
            webhooks.update(
                "wh_123",
                url="https://a.example.com/hook",
                target="https://b.example.com/hook",
            )
        mock_client.put.assert_not_called()


class TestDelete:
    def test_delete_webhook(self, webhooks: Webhooks, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = None
        webhooks.delete("wh_123")
        mock_client.delete.assert_called_once_with("/webhooks/wh_123")
