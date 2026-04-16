"""Tests for the ApiClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from lettr._client import ApiClient
from lettr._exceptions import LettrError


class TestApiClientRequest:
    def test_strips_none_params(self) -> None:
        client = ApiClient(api_key="lttr_test")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "ok"}

        with patch.object(client._http, "request", return_value=mock_response) as mock_req:
            client.get("/test", params={"a": 1, "b": None, "c": "x"})
            _, kwargs = mock_req.call_args
            assert kwargs["params"] == {"a": 1, "c": "x"}

        client.close()

    def test_204_returns_none(self) -> None:
        client = ApiClient(api_key="lttr_test")
        mock_response = MagicMock()
        mock_response.status_code = 204

        with patch.object(client._http, "request", return_value=mock_response):
            result = client.delete("/test")
            assert result is None

        client.close()

    def test_http_error_raises_lettr_error(self) -> None:
        import httpx

        client = ApiClient(api_key="lttr_test")

        with patch.object(
            client._http, "request", side_effect=httpx.ConnectError("connection failed")
        ), pytest.raises(LettrError, match="HTTP request failed"):
            client.get("/test")

        client.close()

    def test_json_parse_failure_on_error_response(self) -> None:
        client = ApiClient(api_key="lttr_test")
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("bad json")

        with patch.object(  # noqa: SIM117
            client._http, "request", return_value=mock_response
        ):
            with pytest.raises(LettrError):
                client.get("/test")

        client.close()


class TestApiClientGetNoAuth:
    @patch("lettr._client.httpx.get")
    def test_get_no_auth_succeeds(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"status": "ok"}}
        mock_get.return_value = mock_response

        client = ApiClient(api_key="lttr_test")
        result = client.get_no_auth("/health")
        assert result == {"data": {"status": "ok"}}

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "Authorization" not in call_kwargs.kwargs.get("headers", {})

        client.close()

    @patch("lettr._client.httpx.get")
    def test_get_no_auth_strips_none_params(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {}}
        mock_get.return_value = mock_response

        client = ApiClient(api_key="lttr_test")
        client.get_no_auth("/health", params={"a": 1, "b": None})

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"] == {"a": 1}

        client.close()


class TestApiClientContextManager:
    def test_context_manager_closes(self) -> None:
        client = ApiClient(api_key="lttr_test")
        with patch.object(client, "close") as mock_close:
            with client:
                pass
            mock_close.assert_called_once()
