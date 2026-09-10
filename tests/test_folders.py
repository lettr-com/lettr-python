"""Tests for the folders resource."""

from __future__ import annotations

from lettr import Lettr
from lettr._types import Folder, FolderList
from lettr.resources.folders import Folders


def folder_payload(folder_id: int, name: str, purpose: str) -> dict:
    return {
        "id": folder_id,
        "name": name,
        "project_id": 5,
        "purpose": purpose,
        "templates_count": 12,
        "created_at": "2026-01-15T10:00:00+00:00",
        "updated_at": "2026-01-20T14:30:00+00:00",
    }


class TestList:
    def test_returns_folders_and_pagination(self, mock_client) -> None:
        mock_client.get.return_value = {
            "data": {
                "folders": [
                    folder_payload(10, "Emails", "transactional"),
                    folder_payload(11, "Campaigns", "campaign"),
                ],
                "pagination": {
                    "total": 2,
                    "per_page": 25,
                    "current_page": 1,
                    "last_page": 1,
                },
            }
        }

        result = Folders(mock_client).list()

        assert isinstance(result, FolderList)
        assert [f.name for f in result.folders] == ["Emails", "Campaigns"]
        assert result.folders[1].purpose == "campaign"
        assert result.folders[0].templates_count == 12
        assert result.total == 2
        mock_client.get.assert_called_once_with("/folders", params={})

    def test_sends_every_filter(self, mock_client) -> None:
        mock_client.get.return_value = {
            "data": {
                "folders": [],
                "pagination": {
                    "total": 0,
                    "per_page": 50,
                    "current_page": 2,
                    "last_page": 2,
                },
            }
        }

        Folders(mock_client).list(project_id=5, purpose="campaign", per_page=50, page=2)

        mock_client.get.assert_called_once_with(
            "/folders",
            params={
                "project_id": 5,
                "purpose": "campaign",
                "per_page": 50,
                "page": 2,
            },
        )

    def test_defaults_a_folder_without_purpose_or_count(self, mock_client) -> None:
        """An API deployment that predates the fields should still parse."""
        mock_client.get.return_value = {
            "data": {
                "folders": [
                    {
                        "id": 10,
                        "name": "Emails",
                        "project_id": 5,
                        "created_at": "2026-01-15T10:00:00+00:00",
                        "updated_at": "2026-01-20T14:30:00+00:00",
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

        folder = Folders(mock_client).list().folders[0]

        assert isinstance(folder, Folder)
        assert folder.purpose == "transactional"
        assert folder.templates_count == 0

    def test_is_reachable_from_the_client(self) -> None:
        assert isinstance(Lettr("test-key").folders, Folders)
