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
        mock_client.get.return_value = {
            "data": {"html": "<p>Hello</p>", "merge_tags": []}
        }

        result = templates.get_html(project_id=5, slug="simple")
        assert isinstance(result, TemplateHtml)
        assert result.html == "<p>Hello</p>"
        assert result.merge_tags == []
        assert result.subject is None
