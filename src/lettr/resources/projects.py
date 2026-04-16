"""Project management."""

from __future__ import annotations

from typing import Any

from .._client import ApiClient
from .._types import Project, ProjectList


class Projects:
    """Operations for retrieving projects.

    Usage::

        projects = client.projects.list()
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        per_page: int | None = None,
        page: int | None = None,
    ) -> ProjectList:
        """List projects with pagination.

        Args:
            per_page: Results per page (1-100, default 25).
            page: Page number (default 1).

        Returns:
            A :class:`ProjectList` with projects and pagination info.
        """
        params: dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page

        body = self._client.get("/projects", params=params)
        data = body["data"]
        pagination = data["pagination"]

        projects = [
            Project(
                id=p["id"],
                name=p["name"],
                team_id=p["team_id"],
                emoji=p.get("emoji"),
                created_at=p["created_at"],
                updated_at=p.get("updated_at"),
            )
            for p in data["projects"]
        ]

        return ProjectList(
            projects=projects,
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )
