"""Tests for the Templates resource."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._types import Template, TemplateHtml, TemplateList, TemplateMergeTags
from lettr.resources.templates import Templates


@pytest.fixture()
def templates(mock_client: MagicMock) -> Templates:
    return Templates(mock_client)


class TestList:
    def test_list_templates(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "templates": [
                    {
                        "id": 1,
                        "name": "Welcome",
                        "slug": "welcome",
                        "project_id": 10,
                        "folder_id": 5,
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

        result = templates.list(project_id=10)
        assert isinstance(result, TemplateList)
        assert len(result.templates) == 1
        assert result.templates[0].slug == "welcome"

        params = mock_client.get.call_args.kwargs["params"]
        assert params["project_id"] == 10


class TestGet:
    def test_get_template(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "id": 1,
                "name": "Welcome",
                "slug": "welcome",
                "project_id": 10,
                "folder_id": 5,
                "created_at": "2025-01-01",
                "active_version": 3,
                "versions_count": 3,
                "html": "<h1>Hi</h1>",
                "updated_at": "2025-06-01",
            }
        }

        result = templates.get("welcome", project_id=10)
        assert isinstance(result, Template)
        assert result.active_version == 3
        assert result.html == "<h1>Hi</h1>"


class TestCreate:
    def test_create_template(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {
                "id": 2,
                "name": "New",
                "slug": "new",
                "project_id": 10,
                "folder_id": 5,
                "active_version": 1,
                "merge_tags": [
                    {"key": "name", "required": True, "type": "text"},
                    {
                        "key": "items",
                        "required": False,
                        "type": "loop",
                        "children": [{"key": "title", "type": "text"}],
                    },
                ],
                "created_at": "2025-01-01",
            }
        }

        result = templates.create(name="New", html="<h1>{{name}}</h1>", project_id=10)
        assert result.slug == "new"
        assert result.merge_tags is not None
        assert len(result.merge_tags) == 2
        assert result.merge_tags[0].key == "name"
        assert result.merge_tags[0].required is True
        assert result.merge_tags[1].children is not None
        assert result.merge_tags[1].children[0].key == "title"


class TestUpdate:
    def test_update_template(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.put.return_value = {
            "data": {
                "id": 1,
                "name": "Updated",
                "slug": "welcome",
                "project_id": 10,
                "folder_id": 5,
                "active_version": 4,
                "created_at": "2025-01-01",
                "updated_at": "2025-06-15",
            }
        }

        result = templates.update("welcome", name="Updated")
        assert result.name == "Updated"
        assert result.updated_at == "2025-06-15"

        payload = mock_client.put.call_args.kwargs["json"]
        assert payload == {"name": "Updated"}


class TestDelete:
    def test_delete_template(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = None
        templates.delete("welcome", project_id=10)
        mock_client.delete.assert_called_once()
        params = mock_client.delete.call_args.kwargs["params"]
        assert params["project_id"] == 10


class TestGetMergeTags:
    def test_get_merge_tags(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "template_slug": "welcome",
                "version": 3,
                "project_id": 10,
                "merge_tags": [
                    {"key": "name", "required": True, "type": "text"},
                ],
            }
        }

        result = templates.get_merge_tags("welcome", project_id=10, version=3)
        assert isinstance(result, TemplateMergeTags)
        assert result.template_slug == "welcome"
        assert result.version == 3
        assert result.project_id == 10
        assert len(result.merge_tags) == 1


class TestGetHtml:
    def test_get_html(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "html": "<h1>Welcome!</h1>",
                "merge_tags": [
                    {"key": "name", "name": "name", "required": True},
                ],
                "subject": "Welcome Email",
            }
        }

        result = templates.get_html(project_id=10, slug="welcome")
        assert isinstance(result, TemplateHtml)
        assert result.html == "<h1>Welcome!</h1>"
        assert result.subject == "Welcome Email"
        assert result.merge_tags is not None
        assert len(result.merge_tags) == 1
        assert result.merge_tags[0].key == "name"
        assert result.merge_tags[0].name == "name"

        params = mock_client.get.call_args.kwargs["params"]
        assert params["project_id"] == 10
        assert params["slug"] == "welcome"
        assert mock_client.get.call_args.args[0] == "/templates/html"

    def test_get_html_empty_merge_tags(self, templates: Templates, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"html": "<p>Hello</p>", "merge_tags": []}}

        result = templates.get_html(project_id=5, slug="simple")
        assert isinstance(result, TemplateHtml)
        assert result.html == "<p>Hello</p>"
        assert result.merge_tags == []
        assert result.subject is None


class TestPreparationStatusAndFolderFilter:
    """Added in 1.6.0 - TPL-2543."""

    def test_list_sends_the_folder_and_purpose_filters(self, mock_client) -> None:
        mock_client.get.return_value = {
            "data": {
                "templates": [],
                "pagination": {
                    "total": 0,
                    "per_page": 100,
                    "current_page": 1,
                    "last_page": 1,
                },
            }
        }

        Templates(mock_client).list(folder_id=10, purpose="campaign", per_page=100)

        mock_client.get.assert_called_once_with(
            "/templates",
            params={"folder_id": 10, "purpose": "campaign", "per_page": 100},
        )

    def test_list_omits_the_new_params_when_unset(self, mock_client) -> None:
        """An existing caller's request is unchanged."""
        mock_client.get.return_value = {
            "data": {
                "templates": [],
                "pagination": {
                    "total": 0,
                    "per_page": 25,
                    "current_page": 1,
                    "last_page": 1,
                },
            }
        }

        Templates(mock_client).list(project_id=5)

        mock_client.get.assert_called_once_with("/templates", params={"project_id": 5})

    def test_list_reads_the_preparation_status_of_every_row(self, mock_client) -> None:
        mock_client.get.return_value = {
            "data": {
                "templates": [
                    {
                        "id": 1,
                        "name": "Ready",
                        "slug": "ready-one",
                        "project_id": 5,
                        "folder_id": 10,
                        "purpose": "transactional",
                        "preparation_status": "ready",
                        "created_at": "2026-01-15T10:00:00+00:00",
                        "updated_at": "2026-01-20T14:30:00+00:00",
                    },
                    {
                        "id": 2,
                        "name": "Working",
                        "slug": "still-working",
                        "project_id": 5,
                        "folder_id": 10,
                        "purpose": "campaign",
                        "preparation_status": "pending",
                        "created_at": "2026-01-15T10:00:00+00:00",
                        "updated_at": "2026-01-20T14:30:00+00:00",
                    },
                ],
                "pagination": {
                    "total": 2,
                    "per_page": 25,
                    "current_page": 1,
                    "last_page": 1,
                },
            }
        }

        templates = Templates(mock_client).list().templates

        assert [t.preparation_status for t in templates] == ["ready", "pending"]
        assert [t.purpose for t in templates] == ["transactional", "campaign"]

    def test_a_response_without_the_fields_reads_as_ready(self, mock_client) -> None:
        """An API deployment that predates the field had every template with
        HTML simply usable, so `ready` is the honest default. `pending` would
        look like a stalled queue and hang anything waiting for readiness."""
        mock_client.get.return_value = {
            "data": {
                "templates": [
                    {
                        "id": 1,
                        "name": "Legacy",
                        "slug": "legacy",
                        "project_id": 5,
                        "folder_id": 10,
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

        template = Templates(mock_client).list().templates[0]

        assert template.preparation_status == "ready"
        assert template.purpose == "transactional"

    def test_create_sends_the_purpose_only_when_given(self, mock_client) -> None:
        mock_client.post.return_value = {
            "data": {
                "id": 1,
                "name": "October Newsletter",
                "slug": "october-newsletter",
                "project_id": 5,
                "folder_id": 11,
                "purpose": "campaign",
                "preparation_status": "pending",
                "active_version": 1,
                "created_at": "2026-01-15T10:00:00+00:00",
            }
        }

        result = Templates(mock_client).create(
            name="October Newsletter", json="{}", purpose="campaign"
        )

        _, kwargs = mock_client.post.call_args
        assert kwargs["json"]["purpose"] == "campaign"
        assert result.purpose == "campaign"
        # A JSON import has no HTML until the background job renders it.
        assert result.preparation_status == "pending"

    def test_create_omits_purpose_when_unset(self, mock_client) -> None:
        mock_client.post.return_value = {
            "data": {
                "id": 1,
                "name": "Welcome",
                "slug": "welcome",
                "project_id": 5,
                "folder_id": 10,
                "created_at": "2026-01-15T10:00:00+00:00",
            }
        }

        Templates(mock_client).create(name="Welcome", html="<p>Hi</p>")

        _, kwargs = mock_client.post.call_args
        assert "purpose" not in kwargs["json"]
