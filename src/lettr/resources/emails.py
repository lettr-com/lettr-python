"""Email sending and retrieval."""

from __future__ import annotations

from typing import Any, Sequence

from .._client import ApiClient
from .._types import (
    Attachment,
    Email,
    EmailDetail,
    EmailEvent,
    EmailEventList,
    EmailList,
    EmailOptions,
    GeoIp,
    ScheduledEmail,
    SendEmailResponse,
    UserAgentParsed,
    _from_dict,
)


def _parse_email(r: dict[str, Any]) -> Email:
    """Parse a raw dict into an Email."""
    return Email(
        event_id=r.get("event_id"),
        type=r.get("type"),
        timestamp=r.get("timestamp"),
        request_id=r.get("request_id"),
        message_id=r.get("message_id"),
        subject=r.get("subject"),
        friendly_from=r.get("friendly_from"),
        sending_domain=r.get("sending_domain"),
        rcpt_to=r.get("rcpt_to"),
        raw_rcpt_to=r.get("raw_rcpt_to"),
        recipient_domain=r.get("recipient_domain"),
        mailbox_provider=r.get("mailbox_provider"),
        mailbox_provider_region=r.get("mailbox_provider_region"),
        sending_ip=r.get("sending_ip"),
        click_tracking=r.get("click_tracking"),
        open_tracking=r.get("open_tracking"),
        transactional=r.get("transactional"),
        msg_size=r.get("msg_size"),
        injection_time=r.get("injection_time"),
        rcpt_meta=r.get("rcpt_meta"),
    )


def _parse_email_event(r: dict[str, Any]) -> EmailEvent:
    """Parse a raw dict into an EmailEvent, handling nested objects."""
    geo_ip = None
    if r.get("geo_ip"):
        geo_ip = _from_dict(GeoIp, r["geo_ip"])
    user_agent_parsed = None
    if r.get("user_agent_parsed"):
        user_agent_parsed = _from_dict(UserAgentParsed, r["user_agent_parsed"])

    return EmailEvent(
        event_id=r.get("event_id"),
        type=r.get("type"),
        timestamp=r.get("timestamp"),
        request_id=r.get("request_id"),
        message_id=r.get("message_id"),
        subject=r.get("subject"),
        friendly_from=r.get("friendly_from"),
        sending_domain=r.get("sending_domain"),
        rcpt_to=r.get("rcpt_to"),
        raw_rcpt_to=r.get("raw_rcpt_to"),
        recipient_domain=r.get("recipient_domain"),
        mailbox_provider=r.get("mailbox_provider"),
        mailbox_provider_region=r.get("mailbox_provider_region"),
        sending_ip=r.get("sending_ip"),
        click_tracking=r.get("click_tracking"),
        open_tracking=r.get("open_tracking"),
        transactional=r.get("transactional"),
        msg_size=r.get("msg_size"),
        injection_time=r.get("injection_time"),
        rcpt_meta=r.get("rcpt_meta"),
        reason=r.get("reason"),
        raw_reason=r.get("raw_reason"),
        error_code=r.get("error_code"),
        bounce_class=r.get("bounce_class"),
        queue_time=r.get("queue_time"),
        outbound_tls=r.get("outbound_tls"),
        num_retries=r.get("num_retries"),
        device_token=r.get("device_token"),
        target_link_url=r.get("target_link_url"),
        target_link_name=r.get("target_link_name"),
        user_agent=r.get("user_agent"),
        ip_address=r.get("ip_address"),
        initial_pixel=r.get("initial_pixel"),
        fbtype=r.get("fbtype"),
        report_by=r.get("report_by"),
        report_to=r.get("report_to"),
        remote_addr=r.get("remote_addr"),
        campaign_id=r.get("campaign_id"),
        template_id=r.get("template_id"),
        template_version=r.get("template_version"),
        ip_pool=r.get("ip_pool"),
        msg_from=r.get("msg_from"),
        rcpt_type=r.get("rcpt_type"),
        rcpt_tags=r.get("rcpt_tags"),
        amp_enabled=r.get("amp_enabled"),
        delv_method=r.get("delv_method"),
        recv_method=r.get("recv_method"),
        routing_domain=r.get("routing_domain"),
        scheduled_time=r.get("scheduled_time"),
        ab_test_id=r.get("ab_test_id"),
        ab_test_version=r.get("ab_test_version"),
        geo_ip=geo_ip,
        user_agent_parsed=user_agent_parsed,
    )


def _parse_scheduled_email(data: dict[str, Any]) -> ScheduledEmail:
    """Parse a raw dict into a ScheduledEmail."""
    return ScheduledEmail(
        transmission_id=data["transmission_id"],
        state=data["state"],
        from_email=data["from"],
        subject=data["subject"],
        recipients=data["recipients"],
        num_recipients=data["num_recipients"],
        events=[_parse_email_event(e) for e in data["events"]],
        scheduled_at=data.get("scheduled_at"),
        from_name=data.get("from_name"),
    )


def _build_email_payload(
    *,
    from_email: str,
    to: Sequence[str],
    subject: str | None = None,
    html: str | None = None,
    text: str | None = None,
    from_name: str | None = None,
    cc: Sequence[str] | None = None,
    bcc: Sequence[str] | None = None,
    reply_to: str | None = None,
    reply_to_name: str | None = None,
    amp_html: str | None = None,
    template_slug: str | None = None,
    template_version: int | None = None,
    project_id: int | None = None,
    tag: str | None = None,
    metadata: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    substitution_data: dict[str, Any] | None = None,
    options: EmailOptions | None = None,
    attachments: Sequence[Attachment] | None = None,
) -> dict[str, Any]:
    """Build the JSON payload for sending or scheduling an email."""
    payload: dict[str, Any] = {
        "from": from_email,
        "to": list(to),
    }

    if subject is not None:
        payload["subject"] = subject
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
    if tag is not None:
        payload["tag"] = tag
    if metadata is not None:
        payload["metadata"] = metadata
    if headers is not None:
        payload["headers"] = headers
    if substitution_data is not None:
        payload["substitution_data"] = substitution_data
    if options is not None:
        payload["options"] = options.to_dict()
    if attachments is not None:
        payload["attachments"] = [
            {"name": a.name, "type": a.type, "data": a.data} for a in attachments
        ]

    return payload


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
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        from_name: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: str | None = None,
        reply_to_name: str | None = None,
        amp_html: str | None = None,
        template_slug: str | None = None,
        template_version: int | None = None,
        project_id: int | None = None,
        tag: str | None = None,
        metadata: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        substitution_data: dict[str, Any] | None = None,
        options: EmailOptions | None = None,
        attachments: Sequence[Attachment] | None = None,
    ) -> SendEmailResponse:
        """Send a transactional email.

        At least one of ``html``, ``text``, or ``template_slug`` must be
        provided.

        Args:
            from_email: Sender email address.
            to: List of recipient email addresses.
            subject: Email subject line. Required unless using a template.
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
            tag: Tracking tag (max 64 characters).
            metadata: Custom metadata for tracking.
            headers: Custom email headers (max 10).
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
            RateLimitError: If sending quota is exceeded.
        """
        payload = _build_email_payload(
            from_email=from_email,
            to=to,
            subject=subject,
            html=html,
            text=text,
            from_name=from_name,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            reply_to_name=reply_to_name,
            amp_html=amp_html,
            template_slug=template_slug,
            template_version=template_version,
            project_id=project_id,
            tag=tag,
            metadata=metadata,
            headers=headers,
            substitution_data=substitution_data,
            options=options,
            attachments=attachments,
        )

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
        per_page: int | None = None,
        cursor: str | None = None,
        recipients: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
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
        params: dict[str, Any] = {}
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
        events = body["data"]["events"]

        results = [_parse_email(r) for r in events["data"]]
        pagination = events.get("pagination", {})

        return EmailList(
            results=results,
            total_count=events["total_count"],
            next_cursor=pagination.get("next_cursor"),
            per_page=pagination.get("per_page", 25),
            date_from=events.get("from"),
            date_to=events.get("to"),
        )

    def get(
        self,
        request_id: str,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> EmailDetail:
        """Get all events for a specific email transmission.

        Args:
            request_id: The ``request_id`` returned when the email was sent.
            from_date: Start date for event search range (ISO 8601).
            to_date: End date for event search range (ISO 8601).

        Returns:
            An :class:`EmailDetail` with all associated events.

        Raises:
            NotFoundError: If the email is not found.
        """
        params: dict[str, Any] = {}
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date

        body = self._client.get(f"/emails/{request_id}", params=params)
        data = body["data"]
        events = [_parse_email_event(r) for r in data["events"]]
        return EmailDetail(
            transmission_id=data["transmission_id"],
            state=data["state"],
            from_email=data["from"],
            subject=data["subject"],
            recipients=data["recipients"],
            num_recipients=data["num_recipients"],
            events=events,
            scheduled_at=data.get("scheduled_at"),
            from_name=data.get("from_name"),
        )

    def list_events(
        self,
        *,
        events: Sequence[str] | None = None,
        recipients: Sequence[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        per_page: int | None = None,
        cursor: str | None = None,
        transmissions: str | None = None,
        bounce_classes: str | None = None,
    ) -> EmailEventList:
        """List email events with filtering.

        Args:
            events: Event types to filter by (e.g. ``["delivery", "bounce"]``).
            recipients: Recipient email addresses to filter by.
            from_date: Start date (ISO 8601). Defaults to 10 days ago.
            to_date: End date (ISO 8601). Defaults to now.
            per_page: Number of events per page.
            cursor: Pagination cursor from a previous response.
            transmissions: Filter by transmission ID.
            bounce_classes: Comma-separated bounce classification codes.

        Returns:
            An :class:`EmailEventList` with events and pagination info.
        """
        params: dict[str, Any] = {}
        if events is not None:
            params["events"] = ",".join(events)
        if recipients is not None:
            params["recipients"] = ",".join(recipients)
        if from_date is not None:
            params["from"] = from_date
        if to_date is not None:
            params["to"] = to_date
        if per_page is not None:
            params["per_page"] = per_page
        if cursor is not None:
            params["cursor"] = cursor
        if transmissions is not None:
            params["transmissions"] = transmissions
        if bounce_classes is not None:
            params["bounce_classes"] = bounce_classes

        body = self._client.get("/emails/events", params=params)
        events_data = body["data"]["events"]

        results = [_parse_email_event(r) for r in events_data["data"]]
        pagination = events_data.get("pagination", {})

        return EmailEventList(
            results=results,
            total_count=events_data["total_count"],
            next_cursor=pagination.get("next_cursor"),
            per_page=pagination.get("per_page", 25),
            date_from=events_data.get("from"),
            date_to=events_data.get("to"),
        )

    def schedule(
        self,
        *,
        from_email: str,
        to: Sequence[str],
        scheduled_at: str,
        subject: str | None = None,
        html: str | None = None,
        text: str | None = None,
        from_name: str | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: str | None = None,
        reply_to_name: str | None = None,
        amp_html: str | None = None,
        template_slug: str | None = None,
        template_version: int | None = None,
        project_id: int | None = None,
        tag: str | None = None,
        metadata: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        substitution_data: dict[str, Any] | None = None,
        options: EmailOptions | None = None,
        attachments: Sequence[Attachment] | None = None,
    ) -> SendEmailResponse:
        """Schedule a transactional email for future delivery.

        Args:
            from_email: Sender email address.
            to: List of recipient email addresses.
            scheduled_at: Scheduled delivery time (ISO 8601).
            subject: Email subject line. Required unless using a template.
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
            tag: Tracking tag (max 64 characters).
            metadata: Custom metadata for tracking.
            headers: Custom email headers (max 10).
            substitution_data: Variables for template substitution.
            options: Delivery options (tracking, etc.).
            attachments: File attachments.

        Returns:
            A :class:`SendEmailResponse` with ``request_id``, ``accepted``,
            and ``rejected`` counts. Use :meth:`get_scheduled` with the
            ``request_id`` to retrieve the full scheduled transmission.

        Raises:
            ValidationError: If required fields are missing or invalid.
            ForbiddenError: If scheduling is not permitted.
            RateLimitError: If sending quota is exceeded.
        """
        payload = _build_email_payload(
            from_email=from_email,
            to=to,
            subject=subject,
            html=html,
            text=text,
            from_name=from_name,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            reply_to_name=reply_to_name,
            amp_html=amp_html,
            template_slug=template_slug,
            template_version=template_version,
            project_id=project_id,
            tag=tag,
            metadata=metadata,
            headers=headers,
            substitution_data=substitution_data,
            options=options,
            attachments=attachments,
        )
        payload["scheduled_at"] = scheduled_at

        body = self._client.post("/emails/scheduled", json=payload)
        data = body["data"]
        return SendEmailResponse(
            request_id=data["request_id"],
            accepted=data["accepted"],
            rejected=data["rejected"],
        )

    def get_scheduled(self, transmission_id: str) -> ScheduledEmail:
        """Get details of a scheduled email transmission.

        Args:
            transmission_id: The transmission ID.

        Returns:
            A :class:`ScheduledEmail` with the transmission details.

        Raises:
            NotFoundError: If the transmission is not found.
            ForbiddenError: If access is not permitted.
        """
        body = self._client.get(f"/emails/scheduled/{transmission_id}")
        return _parse_scheduled_email(body["data"])

    def cancel_scheduled(self, transmission_id: str) -> None:
        """Cancel a scheduled email transmission before it is sent.

        Args:
            transmission_id: The transmission ID to cancel.

        Raises:
            NotFoundError: If the transmission is not found.
            ConflictError: If the transmission has already been sent.
            ForbiddenError: If cancellation is not permitted.
        """
        self._client.delete(f"/emails/scheduled/{transmission_id}")
