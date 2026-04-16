"""Tests for the Projects resource."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._types import ProjectList
from lettr.resources.projects import Projects


@pytest.fixture()
def projects(mock_client: MagicMock) -> Projects:
    return Projects(mock_client)


class TestList:
    def test_list_projects(self, projects: Projects, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "projects": [
                    {
                        "id": 1,
                        "name": "Main",
                        "team_id": 10,
                        "emoji": "🚀",
                        "created_at": "2025-01-01",
                        "updated_at": "2025-06-01",
                    }
                ],
                "pagination": {
                    "total": 1,
                    "per_page": 25,
                    "current_page": 1,
                    "last_page": 1,
                },
            }
        }

        result = projects.list()
        assert isinstance(result, ProjectList)
        assert len(result.projects) == 1
        assert result.projects[0].name == "Main"
        assert result.projects[0].emoji == "🚀"
        assert result.total == 1

    def test_list_with_pagination(self, projects: Projects, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "projects": [],
                "pagination": {
                    "total": 0,
                    "per_page": 10,
                    "current_page": 2,
                    "last_page": 2,
                },
            }
        }

        projects.list(per_page=10, page=2)
        params = mock_client.get.call_args.kwargs["params"]
        assert params["per_page"] == 10
        assert params["page"] == 2
