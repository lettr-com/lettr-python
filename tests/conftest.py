"""Shared test fixtures."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._client import ApiClient


@pytest.fixture()
def mock_client() -> MagicMock:
    """Return a mocked ApiClient whose HTTP methods can be configured per test."""
    client = MagicMock(spec=ApiClient)
    client._base_url = "https://app.lettr.com/api"
    return client
