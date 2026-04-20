"""Low-level HTTP client for the Lettr API."""

from __future__ import annotations

from typing import Any

import httpx

from ._exceptions import LettrError, raise_for_status

DEFAULT_BASE_URL = "https://app.lettr.com/api"
DEFAULT_TIMEOUT = 30.0


class ApiClient:
    """Thin wrapper around ``httpx.Client`` with auth and error handling."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "lettr-python/1.0.0",
            },
        )

    # -- HTTP helpers -------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send an HTTP request and return the decoded JSON body.

        Raises the appropriate :class:`LettrError` subclass on non-2xx
        responses.
        """
        # Strip None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            response = self._http.request(method, path, json=json, params=params)
        except httpx.HTTPError as exc:
            raise LettrError(f"HTTP request failed: {exc}") from exc

        if response.status_code == 204:
            return None

        try:
            body = response.json()
        except Exception:
            raise_for_status(response.status_code, None)
            return None

        raise_for_status(response.status_code, body)
        return body

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, json=json)

    def put(self, path: str, *, json: dict[str, Any] | None = None) -> Any:
        return self.request("PUT", path, json=json)

    def delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("DELETE", path, params=params)

    def get_no_auth(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request without the Authorization header.

        Used for endpoints that don't require authentication (e.g. health check).
        """
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            response = httpx.get(
                f"{self._base_url}{path}",
                params=params,
                timeout=self._timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "lettr-python/1.0.0",
                },
            )
        except httpx.HTTPError as exc:
            raise LettrError(f"HTTP request failed: {exc}") from exc

        try:
            body = response.json()
        except Exception:
            raise_for_status(response.status_code, None)
            return None

        raise_for_status(response.status_code, body)
        return body

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
