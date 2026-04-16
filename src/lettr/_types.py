"""Type definitions for the Lettr SDK."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, TypeVar

T = TypeVar("T")


def _from_dict(cls: type[T], data: dict[str, Any]) -> T:
    """Build a dataclass instance from a dict, ignoring unknown keys.

    Server payloads may add new fields over time; using bare ``cls(**data)``
    crashes on the first unknown key. This helper filters ``data`` to only
    the fields declared on ``cls`` so that forward-compatible parsing works.
    """
    known = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    return cls(**{k: v for k, v in data.items() if k in known})

# ---------------------------------------------------------------------------
# Common / shared types
# ---------------------------------------------------------------------------


@dataclass
class HealthCheck:
    """Response from the health check endpoint."""

    status: str
    timestamp: str


@dataclass
class AuthCheck:
    """Response from the auth check endpoint."""

    team_id: int
    timestamp: str


@dataclass
class GeoIp:
    """Geolocation data associated with an email event."""

    country: str | None = None
    region: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    zip: str | None = None
    postal_code: str | None = None


@dataclass
class UserAgentParsed:
    """Parsed user-agent data associated with an email event."""

    agent_family: str | None = None
    device_brand: str | None = None
    device_family: str | None = None
    os_family: str | None = None
    os_version: str | None = None
    is_mobile: bool | None = None
    is_proxy: bool | None = None
    is_prefetched: bool | None = None


# ---------------------------------------------------------------------------
# Email types
# ---------------------------------------------------------------------------


@dataclass
class Attachment:
    """An email file attachment."""

    name: str
    """Filename of the attachment (e.g. ``"invoice.pdf"``)."""

    type: str
    """MIME type (e.g. ``"application/pdf"``)."""

    data: str
    """Base64-encoded file content (no line breaks)."""


@dataclass
class EmailOptions:
    """Delivery options for an email."""

    click_tracking: bool | None = None
    open_tracking: bool | None = None
    transactional: bool | None = None
    inline_css: bool | None = None
    perform_substitutions: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class SendEmailResponse:
    """Response from sending an email."""

    request_id: str
    accepted: int
    rejected: int


@dataclass
class Email:
    """A sent email event."""

    event_id: str | None = None
    type: str | None = None
    timestamp: str | None = None
    request_id: str | None = None
    message_id: str | None = None
    subject: str | None = None
    friendly_from: str | None = None
    sending_domain: str | None = None
    rcpt_to: str | None = None
    raw_rcpt_to: str | None = None
    recipient_domain: str | None = None
    mailbox_provider: str | None = None
    mailbox_provider_region: str | None = None
    sending_ip: str | None = None
    click_tracking: bool | None = None
    open_tracking: bool | None = None
    transactional: bool | None = None
    msg_size: int | None = None
    injection_time: str | None = None
    rcpt_meta: dict[str, Any] | None = None


@dataclass
class EmailEvent(Email):
    """A detailed email event including type and error info."""

    reason: str | None = None
    raw_reason: str | None = None
    error_code: str | None = None
    campaign_id: str | None = None
    template_id: str | None = None
    template_version: str | None = None
    ip_pool: str | None = None
    msg_from: str | None = None
    rcpt_type: str | None = None
    rcpt_tags: list[str] | None = None
    amp_enabled: bool | None = None
    delv_method: str | None = None
    recv_method: str | None = None
    routing_domain: str | None = None
    scheduled_time: str | None = None
    ab_test_id: str | None = None
    ab_test_version: str | None = None
    geo_ip: GeoIp | None = None
    user_agent_parsed: UserAgentParsed | None = None


@dataclass
class EmailList:
    """Paginated list of sent emails."""

    results: list[Email]
    total_count: int
    next_cursor: str | None = None
    per_page: int = 25
    date_from: str | None = None
    date_to: str | None = None


@dataclass
class EmailDetail:
    """Detailed email with its delivery events."""

    transmission_id: str
    state: str
    from_email: str
    subject: str
    recipients: list[str]
    num_recipients: int
    events: list[EmailEvent]
    scheduled_at: str | None = None
    from_name: str | None = None


@dataclass
class EmailEventList:
    """Paginated list of email events."""

    results: list[EmailEvent]
    total_count: int
    next_cursor: str | None = None
    per_page: int = 25
    date_from: str | None = None
    date_to: str | None = None


@dataclass
class ScheduledEmail:
    """A scheduled email transmission (same shape as :class:`EmailDetail`)."""

    transmission_id: str
    state: str
    from_email: str
    subject: str
    recipients: list[str]
    num_recipients: int
    events: list[EmailEvent]
    scheduled_at: str | None = None
    from_name: str | None = None


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class DkimInfo:
    """DKIM configuration for a domain."""

    public: str | None = None
    selector: str | None = None
    headers: str | None = None
    signing_domain: str | None = None


@dataclass
class DmarcValidationResult:
    """DMARC DNS validation result."""

    is_valid: bool | None = None
    status: str | None = None
    found_at_domain: str | None = None
    record: str | None = None
    policy: str | None = None
    subdomain_policy: str | None = None
    error: str | None = None
    covered_by_parent_policy: bool | None = None


@dataclass
class SpfValidationResult:
    """SPF DNS validation result."""

    is_valid: bool | None = None
    status: str | None = None
    record: str | None = None
    error: str | None = None
    includes_sparkpost: bool | None = None


@dataclass
class Domain:
    """A sending domain."""

    domain: str
    status: str
    status_label: str
    can_send: bool | None = None
    cname_status: str | None = None
    dkim_status: str | None = None
    dmarc_status: str | None = None
    spf_status: str | None = None
    is_primary_domain: bool | None = None
    tracking_domain: str | None = None
    dns: dict[str, Any] | None = None
    dns_provider: str | None = None
    dkim: DkimInfo | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class DomainVerification:
    """Domain verification result."""

    domain: str
    dkim_status: str
    cname_status: str
    dmarc_status: str | None = None
    spf_status: str | None = None
    is_primary_domain: bool | None = None
    ownership_verified: str | None = None
    dns: dict[str, Any] | None = None
    dmarc: DmarcValidationResult | None = None
    spf: SpfValidationResult | None = None


# ---------------------------------------------------------------------------
# Webhook types
# ---------------------------------------------------------------------------


@dataclass
class Webhook:
    """A webhook configuration."""

    id: str
    name: str
    url: str
    enabled: bool
    auth_type: str
    has_auth_credentials: bool
    event_types: list[str] | None = None
    last_successful_at: str | None = None
    last_failure_at: str | None = None
    last_status: str | None = None


# ---------------------------------------------------------------------------
# Template types
# ---------------------------------------------------------------------------


@dataclass
class MergeTagChild:
    """A child merge tag within a loop block."""

    key: str
    type: str | None = None


@dataclass
class MergeTag:
    """A template merge tag."""

    key: str
    required: bool = False
    type: str | None = None
    children: list[MergeTagChild] | None = None


@dataclass
class Template:
    """An email template."""

    id: int
    name: str
    slug: str
    project_id: int
    folder_id: int
    created_at: str
    updated_at: str | None = None
    active_version: int | None = None
    versions_count: int | None = None
    html: str | None = None
    json: str | None = None
    merge_tags: list[MergeTag] | None = None


@dataclass
class TemplateList:
    """Paginated list of templates."""

    templates: list[Template]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class TemplateMergeTags:
    """Merge tags for a template version."""

    template_slug: str
    version: int
    merge_tags: list[MergeTag]
    project_id: int | None = None


# ---------------------------------------------------------------------------
# Project types
# ---------------------------------------------------------------------------


@dataclass
class Project:
    """A project."""

    id: int
    name: str
    team_id: int
    created_at: str
    emoji: str | None = None
    updated_at: str | None = None


@dataclass
class ProjectList:
    """Paginated list of projects."""

    projects: list[Project]
    total: int
    per_page: int
    current_page: int
    last_page: int
