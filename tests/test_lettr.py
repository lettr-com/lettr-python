"""Tests for the Lettr main client class."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr import AuthCheck, HealthCheck, Lettr


class TestLettrConstructor:
    def test_empty_api_key_raises(self) -> None:
        with pytest.raises(ValueError, match="api_key parameter is required"):
            Lettr("")

    def test_creates_resources(self) -> None:
        client = Lettr("lttr_test")
        assert hasattr(client, "emails")
        assert hasattr(client, "domains")
        assert hasattr(client, "templates")
        assert hasattr(client, "webhooks")
        assert hasattr(client, "projects")
        client.close()

    def test_repr(self) -> None:
        client = Lettr("lttr_test")
        assert "app.lettr.com" in repr(client)
        client.close()


class TestLettrContextManager:
    def test_context_manager(self) -> None:
        with Lettr("lttr_test") as client:
            assert client is not None


class TestLettrHealth:
    def test_health(self) -> None:
        client = Lettr("lttr_test")
        client._client.get_no_auth = MagicMock(
            return_value={"data": {"status": "ok", "timestamp": "2024-01-15T10:30:00Z"}}
        )

        result = client.health()
        assert isinstance(result, HealthCheck)
        assert result.status == "ok"
        assert result.timestamp == "2024-01-15T10:30:00Z"
        client._client.get_no_auth.assert_called_once_with("/health")
        client.close()


class TestLettrAuthCheck:
    def test_auth_check(self) -> None:
        client = Lettr("lttr_test")
        client._client.get = MagicMock(
            return_value={"data": {"team_id": 1, "timestamp": "2024-01-15T10:30:00Z"}}
        )

        result = client.auth_check()
        assert isinstance(result, AuthCheck)
        assert result.team_id == 1
        assert result.timestamp == "2024-01-15T10:30:00Z"
        client._client.get.assert_called_once_with("/auth/check")
        client.close()
