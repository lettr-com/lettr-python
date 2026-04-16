"""Email template management."""

from __future__ import annotations

from typing import Any

from .._client import ApiClient
from .._types import (
    MergeTag,
    MergeTagChild,
    Template,
    TemplateHtml,
    TemplateList,
    TemplateMergeTags,
)


def _parse_merge_tags(raw: list[dict[str, Any]]) -> list[MergeTag]:
    tags: list[MergeTag] = []
    for t in raw:
        children = None
        if t.get("children"):
            children = [MergeTagChild(key=c["key"], type=c.get("type")) for c in t["children"]]
        tags.append(
            MergeTag(
                key=t["key"],
                required=t.get("required", False),
                type=t.get("type"),
                name=t.get("name"),
                children=children,
            )
        )
    return tags


class Templates:
    """Operations for managing email templates.

    Usage::

        templates = client.templates.list()
        template = client.templates.create(
            name="Welcome Email",
            html="<h1>Welcome {{NAME}}!</h1>",
        )
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        project_id: int | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> TemplateList:
        """List email templates with pagination.

        Args:
            project_id: Project ID to retrieve templates from.
                If not provided, uses the team's default project.
            per_page: Results per page (1-100, default 25).
            page: Page number (default 1).

        Returns:
            A :class:`TemplateList` with templates and pagination info.
        """
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page

        body = self._client.get("/templates", params=params)
        data = body["data"]
        pagination = data["pagination"]

        templates = [
            Template(
                id=t["id"],
                name=t["name"],
                slug=t["slug"],
                project_id=t["project_id"],
                folder_id=t["folder_id"],
                created_at=t["created_at"],
                updated_at=t["updated_at"],
            )
            for t in data["templates"]
        ]

        return TemplateList(
            templates=templates,
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )

    def get(self, slug: str, *, project_id: int | None = None) -> Template:
        """Get a single template by slug.

        Args:
            slug: The template slug (URL-friendly identifier).
            project_id: Project ID to look up the template in.

        Returns:
            A :class:`Template` with full details.

        Raises:
            NotFoundError: If the template or project is not found.
        """
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id

        body = self._client.get(f"/templates/{slug}", params=params)
        d = body["data"]
        return Template(
            id=d["id"],
            name=d["name"],
            slug=d["slug"],
            project_id=d["project_id"],
            folder_id=d["folder_id"],
            created_at=d["created_at"],
            updated_at=d.get("updated_at"),
            active_version=d.get("active_version"),
            versions_count=d["versions_count"],
            html=d.get("html"),
            json=d.get("json"),
        )

    def create(
        self,
        *,
        name: str,
        html: str | None = None,
        json: str | None = None,
        project_id: int | None = None,
        folder_id: int | None = None,
    ) -> Template:
        """Create a new email template.

        Provide either ``html`` for custom HTML templates or ``json`` for
        Topol visual editor templates.

        Args:
            name: Name of the template.
            html: HTML content. Mutually exclusive with ``json``.
            json: Topol JSON content. Mutually exclusive with ``html``.
            project_id: Project to create the template in.
            folder_id: Folder to create the template in.

        Returns:
            A :class:`Template` with the newly created template info.

        Raises:
            ValidationError: If validation fails.
            NotFoundError: If the project or folder is not found.
        """
        payload: dict[str, Any] = {"name": name}
        if html is not None:
            payload["html"] = html
        if json is not None:
            payload["json"] = json
        if project_id is not None:
            payload["project_id"] = project_id
        if folder_id is not None:
            payload["folder_id"] = folder_id

        body = self._client.post("/templates", json=payload)
        d = body["data"]

        merge_tags = None
        if d.get("merge_tags"):
            merge_tags = _parse_merge_tags(d["merge_tags"])

        return Template(
            id=d["id"],
            name=d["name"],
            slug=d["slug"],
            project_id=d["project_id"],
            folder_id=d["folder_id"],
            active_version=d.get("active_version"),
            merge_tags=merge_tags,
            created_at=d["created_at"],
        )

    def update(
        self,
        slug: str,
        *,
        name: str | None = None,
        html: str | None = None,
        json: str | None = None,
        project_id: int | None = None,
    ) -> Template:
        """Update an existing email template.

        If ``html`` or ``json`` content is provided, a new active version will
        be created with extracted merge tags.

        Args:
            slug: The template slug to update.
            name: New name for the template.
            html: New HTML content. Mutually exclusive with ``json``.
            json: New Topol JSON content. Mutually exclusive with ``html``.
            project_id: Project ID to find the template in.

        Returns:
            A :class:`Template` with the updated info.

        Raises:
            NotFoundError: If the template or project is not found.
            ValidationError: If validation fails.
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if html is not None:
            payload["html"] = html
        if json is not None:
            payload["json"] = json
        if project_id is not None:
            payload["project_id"] = project_id

        body = self._client.put(f"/templates/{slug}", json=payload)
        d = body["data"]

        merge_tags = None
        if d.get("merge_tags"):
            merge_tags = _parse_merge_tags(d["merge_tags"])

        return Template(
            id=d["id"],
            name=d["name"],
            slug=d["slug"],
            project_id=d["project_id"],
            folder_id=d["folder_id"],
            active_version=d.get("active_version"),
            merge_tags=merge_tags,
            created_at=d["created_at"],
            updated_at=d.get("updated_at"),
        )

    def delete(self, slug: str, *, project_id: int | None = None) -> None:
        """Permanently delete a template and all its versions.

        Args:
            slug: The template slug to delete.
            project_id: Project ID to find the template in.

        Raises:
            NotFoundError: If the template or project is not found.
        """
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        self._client.delete(f"/templates/{slug}", params=params)

    def get_merge_tags(
        self,
        slug: str,
        *,
        project_id: int | None = None,
        version: int | None = None,
    ) -> TemplateMergeTags:
        """Get merge tags for a template version.

        Args:
            slug: The template slug.
            project_id: Project ID to find the template in.
            version: Template version number. Defaults to the active version.

        Returns:
            A :class:`TemplateMergeTags` with the list of merge tags.

        Raises:
            NotFoundError: If the template or project is not found.
        """
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        if version is not None:
            params["version"] = version

        body = self._client.get(f"/templates/{slug}/merge-tags", params=params)
        d = body["data"]
        return TemplateMergeTags(
            template_slug=d["template_slug"],
            version=d["version"],
            merge_tags=_parse_merge_tags(d["merge_tags"]),
            project_id=d.get("project_id"),
        )

    def get_html(self, *, project_id: int, slug: str) -> TemplateHtml:
        """Get the rendered HTML and merge tags of a template.

        Args:
            project_id: Project ID containing the template.
            slug: The template slug.

        Returns:
            A :class:`TemplateHtml` with ``html``, ``merge_tags``, and
            ``subject``.

        Raises:
            NotFoundError: If the template or project is not found.
        """
        params: dict[str, Any] = {
            "project_id": project_id,
            "slug": slug,
        }
        body = self._client.get("/templates/html", params=params)
        d = body["data"]
        merge_tags = _parse_merge_tags(d.get("merge_tags", []))
        return TemplateHtml(
            html=d["html"],
            merge_tags=merge_tags,
            subject=d.get("subject"),
        )
