"""Email sending and retrieval."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .._client import ApiClient
from .._types import (
    Attachment,
    Email,
    EmailDetail,
    EmailEvent,
    EmailList,
    EmailOptions,
    SendEmailResponse,
)


class Emails:
    """Operations for sending and retrieving emails.

    Usage::

        response = client.emails.send(
            from_email="sender@example.com",
            to=["recipient@example.com"],
            subject="Hello",
            html="<p>Hello!</p>",
        )
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def send(
        self,
        *,
        from_email: str,
        to: Sequence[str],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        from_name: Optional[str] = None,
        cc: Optional[Sequence[str]] = None,
        bcc: Optional[Sequence[str]] = None,
        reply_to: Optional[str] = None,
        reply_to_name: Optional[str] = None,
        amp_html: Optional[str] = None,
        template_slug: Optional[str] = None,
        template_version: Optional[int] = None,
        project_id: Optional[int] = None,
        campaign_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        substitution_data: Optional[Dict[str, Any]] = None,
        options: Optional[EmailOptions] = None,
        attachments: Optional[Sequence[Attachment]] = None,
    ) -> SendEmailResponse:
        """Send a transactional email.

        At least one of ``html``, ``text``, or ``template_slug`` must be
        provided.

        Args:
            from_email: Sender email address.
            to: List of recipient email addresses.
            subject: Email subject line.
            html: HTML content of the email.
            text: Plain text content of the email.
            from_name: Sender display name.
            cc: Carbon copy recipients.
            bcc: Blind carbon copy recipients.
            reply_to: Reply-To email address.
            reply_to_name: Reply-To display name.
            amp_html: AMP HTML content.
            template_slug: Template slug to use for content.
            template_version: Specific template version number.
            project_id: Project ID containing the template.
            campaign_id: Campaign identifier for tracking.
            metadata: Custom metadata for tracking.
            substitution_data: Variables for template substitution.
            options: Delivery options (tracking, etc.).
            attachments: File attachments.

        Returns:
            A :class:`SendEmailResponse` with ``request_id``, ``accepted``,
            and ``rejected`` counts.

        Raises:
            ValidationError: If required fields are missing or invalid.
            BadRequestError: If the sender domain is invalid or unconfigured.
            NotFoundError: If the template or project is not found.
        """
        payload: Dict[str, Any] = {
            "from": from_email,
            "to": list(to),
            "subject": subject,
        }

        if html is not None:
            payload["html"] = html
        if text is not None:
            payload["text"] = text
        if from_name is not None:
            payload["from_name"] = from_name
        if cc is not None:
            payload["cc"] = list(cc)
        if bcc is not None:
            payload["bcc"] = list(bcc)
        if reply_to is not None:
            payload["reply_to"] = reply_to
        if reply_to_name is not None:
            payload["reply_to_name"] = reply_to_name
        if amp_html is not None:
            payload["amp_html"] = amp_html
        if template_slug is not None:
            payload["template_slug"] = template_slug
        if template_version is not None:
            payload["template_version"] = template_version
        if project_id is not None:
            payload["project_id"] = project_id
        if campaign_id is not None:
            payload["campaign_id"] = campaign_id
        if metadata is not None:
            payload["metadata"] = metadata
        if substitution_data is not None:
            payload["substitution_data"] = substitution_data
        if options is not None:
            payload["options"] = options.to_dict()
        if attachments is not None:
            payload["attachments"] = [
                {"name": a.name, "type": a.type, "data": a.data} for a in attachments
            ]

        body = self._client.post("/emails", json=payload)
        data = body["data"]
        return SendEmailResponse(
            request_id=data["request_id"],
            accepted=data["accepted"],
            rejected=data["rejected"],
        )

    def list(
        self,
        *,
        per_page: Optional[int] = None,
        cursor: Optional[str] = None,
        recipients: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> EmailList:
        """List sent emails with cursor-based pagination.

        Args:
            per_page: Results per page (1-100, default 25).
            cursor: Pagination cursor from a previous response.
            recipients: Filter by recipient email address.
            from_date: Filter emails sent on or after this date (ISO 8601).
            to_date: Filter emails sent on or before this date (ISO 8601).

        Returns:
            An :class:`EmailList` with results and pagination info.
        """
        params: Dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if cursor is not None:
            params["cursor"] = cursor
        if recipients is not None:
            params["recipients"] = recipients
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date

        body = self._client.get("/emails", params=params)
        data = body["data"]

        results = [Email(**r) for r in data["results"]]
        pagination = data.get("pagination", {})

        return EmailList(
            results=results,
            total_count=data["total_count"],
            next_cursor=pagination.get("next_cursor"),
            per_page=pagination.get("per_page", 25),
        )

    def get(self, request_id: str) -> EmailDetail:
        """Get all events for a specific email transmission.

        Args:
            request_id: The ``request_id`` returned when the email was sent.

        Returns:
            An :class:`EmailDetail` with all associated events.

        Raises:
            NotFoundError: If the email is not found.
        """
        body = self._client.get(f"/emails/{request_id}")
        data = body["data"]
        results = [EmailEvent(**r) for r in data["results"]]
        return EmailDetail(results=results, total_count=data["total_count"])
