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

from ._client import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, ApiClient
from ._exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    LettrError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from ._types import (
    Attachment,
    AuthCheck,
    DkimInfo,
    DmarcValidationResult,
    DnsProvider,
    Domain,
    DomainDnsVerification,
    DomainVerification,
    Email,
    EmailDetail,
    EmailEvent,
    EmailEventList,
    EmailList,
    EmailOptions,
    GeoIp,
    HealthCheck,
    MergeTag,
    MergeTagChild,
    Project,
    ProjectList,
    ScheduledEmail,
    SendEmailResponse,
    SpfValidationResult,
    Template,
    TemplateHtml,
    TemplateList,
    TemplateMergeTags,
    UserAgentParsed,
    Webhook,
)
from .resources import Domains, Emails, Projects, Templates, Webhooks

__version__ = "1.0.0"

__all__ = [
    # Client
    "Lettr",
    # Exceptions
    "LettrError",
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    # Types
    "Attachment",
    "AuthCheck",
    "DkimInfo",
    "DmarcValidationResult",
    "DnsProvider",
    "Domain",
    "DomainDnsVerification",
    "DomainVerification",
    "Email",
    "EmailDetail",
    "EmailEvent",
    "EmailEventList",
    "EmailList",
    "EmailOptions",
    "GeoIp",
    "HealthCheck",
    "MergeTag",
    "MergeTagChild",
    "Project",
    "ProjectList",
    "ScheduledEmail",
    "SendEmailResponse",
    "SpfValidationResult",
    "Template",
    "TemplateHtml",
    "TemplateList",
    "TemplateMergeTags",
    "UserAgentParsed",
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
                "The api_key parameter is required. Get your API key at https://app.lettr.com"
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

    def health(self) -> HealthCheck:
        """Check API health. No authentication required.

        Returns:
            A :class:`HealthCheck` with the API status.
        """
        body = self._client.get_no_auth("/health")
        data = body["data"]
        return HealthCheck(status=data["status"], timestamp=data["timestamp"])

    def auth_check(self) -> AuthCheck:
        """Validate the API key and return team information.

        Returns:
            An :class:`AuthCheck` with team details.

        Raises:
            AuthenticationError: If the API key is invalid.
        """
        body = self._client.get("/auth/check")
        data = body["data"]
        return AuthCheck(
            team_id=data["team_id"],
            timestamp=data["timestamp"],
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> Lettr:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Lettr(base_url={self._client._base_url!r})"
