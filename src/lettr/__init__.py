"""Lettr — Official Python SDK for the Lettr Email API.

Usage::

    import lettr

    client = lettr.Lettr("your_api_key")

    client.emails.send(
        from_email="you@example.com",
        to=["user@example.com"],
        subject="Hello from Lettr!",
        html="<h1>Hello!</h1>",
    )
"""

from __future__ import annotations

from typing import Optional

from ._client import ApiClient, DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from ._exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    LettrError,
    NotFoundError,
    ServerError,
    ValidationError,
)
from ._types import (
    Attachment,
    Domain,
    DomainVerification,
    Email,
    EmailDetail,
    EmailEvent,
    EmailList,
    EmailOptions,
    MergeTag,
    Project,
    ProjectList,
    SendEmailResponse,
    Template,
    TemplateList,
    TemplateMergeTags,
    Webhook,
)
from .resources import Domains, Emails, Projects, Templates, Webhooks

__version__ = "0.1.0"

__all__ = [
    # Client
    "Lettr",
    # Exceptions
    "LettrError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "NotFoundError",
    "ServerError",
    "ValidationError",
    # Types
    "Attachment",
    "Domain",
    "DomainVerification",
    "Email",
    "EmailDetail",
    "EmailEvent",
    "EmailList",
    "EmailOptions",
    "MergeTag",
    "Project",
    "ProjectList",
    "SendEmailResponse",
    "Template",
    "TemplateList",
    "TemplateMergeTags",
    "Webhook",
]


class Lettr:
    """The Lettr API client.

    Provides access to all Lettr API resources through a clean,
    resource-based interface.

    Args:
        api_key: Your Lettr API key (starts with ``lttr_``).
        base_url: API base URL. Defaults to ``https://app.lettr.com/api``.
        timeout: Request timeout in seconds. Defaults to 30.

    Usage::

        import lettr

        client = lettr.Lettr("lttr_your_api_key")

        # Send an email
        response = client.emails.send(
            from_email="sender@example.com",
            to=["recipient@example.com"],
            subject="Hello!",
            html="<p>Welcome!</p>",
        )
        print(response.request_id)

        # List domains
        domains = client.domains.list()

        # Use as context manager
        with lettr.Lettr("lttr_your_api_key") as client:
            client.emails.send(...)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError(
                "The api_key parameter is required. "
                "Get your API key at https://app.lettr.com"
            )

        self._client = ApiClient(api_key=api_key, base_url=base_url, timeout=timeout)

        self.emails = Emails(self._client)
        """Email sending and retrieval operations."""

        self.domains = Domains(self._client)
        """Domain management operations."""

        self.templates = Templates(self._client)
        """Email template management operations."""

        self.webhooks = Webhooks(self._client)
        """Webhook management operations."""

        self.projects = Projects(self._client)
        """Project management operations."""

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "Lettr":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Lettr(base_url={self._client._base_url!r})"
