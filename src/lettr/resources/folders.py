"""Template folder listing."""

from __future__ import annotations

from typing import Any

from .._client import ApiClient
from .._types import Folder, FolderList, TemplatePurpose


class Folders:
    """Read-only operations for template folders.

    Creating, renaming and deleting folders stay in the app, because deleting
    one moves or deletes the templates inside it.

    Usage::

        folders = client.folders.list(purpose="campaign")
        client.templates.create(
            name="October Newsletter",
            json=topol_json,
            folder_id=folders.folders[0].id,
            purpose="campaign",
        )
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        project_id: int | None = None,
        purpose: TemplatePurpose | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> FolderList:
        """List the folders templates are filed into.

        This is what :meth:`Templates.create`'s ``folder_id`` was missing:
        nothing else returns a folder id, so a caller either omitted it and
        accepted whichever folder the API picked, or hardcoded an integer read
        out of an app URL.

        Args:
            project_id: Project to list folders from. Without one the team's
                default project is used, as ``templates.list()`` does.
            purpose: Narrow to one module. Omit for both.
            per_page: Results per page (1-100, default 25).
            page: Page number (default 1).

        Returns:
            A :class:`FolderList` with folders and pagination info.

        Raises:
            NotFoundError: If the project is not found or belongs to another team.
        """
        params: dict[str, Any] = {}
        if project_id is not None:
            params["project_id"] = project_id
        if purpose is not None:
            params["purpose"] = purpose
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page

        body = self._client.get("/folders", params=params)
        data = body["data"]
        pagination = data["pagination"]

        folders = [
            Folder(
                id=f["id"],
                name=f["name"],
                project_id=f["project_id"],
                purpose=f.get("purpose", "transactional"),
                templates_count=f.get("templates_count", 0),
                created_at=f["created_at"],
                updated_at=f["updated_at"],
            )
            for f in data["folders"]
        ]

        return FolderList(
            folders=folders,
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )
