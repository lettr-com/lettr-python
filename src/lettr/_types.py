"""Type definitions for the Lettr SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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

    click_tracking: Optional[bool] = None
    open_tracking: Optional[bool] = None
    transactional: Optional[bool] = None
    inline_css: Optional[bool] = None
    perform_substitutions: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
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

    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None
    message_id: Optional[str] = None
    subject: Optional[str] = None
    friendly_from: Optional[str] = None
    sending_domain: Optional[str] = None
    rcpt_to: Optional[str] = None
    raw_rcpt_to: Optional[str] = None
    recipient_domain: Optional[str] = None
    mailbox_provider: Optional[str] = None
    mailbox_provider_region: Optional[str] = None
    sending_ip: Optional[str] = None
    click_tracking: Optional[bool] = None
    open_tracking: Optional[bool] = None
    transactional: Optional[bool] = None
    msg_size: Optional[int] = None
    injection_time: Optional[str] = None
    rcpt_meta: Optional[Dict[str, Any]] = None


@dataclass
class EmailEvent(Email):
    """A detailed email event including type and error info."""

    type: Optional[str] = None
    reason: Optional[str] = None
    raw_reason: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class EmailList:
    """Paginated list of sent emails."""

    results: List[Email]
    total_count: int
    next_cursor: Optional[str] = None
    per_page: int = 25


@dataclass
class EmailDetail:
    """Detailed email with all events."""

    results: List[EmailEvent]
    total_count: int


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass
class DkimInfo:
    """DKIM configuration for a domain."""

    public: Optional[str] = None
    selector: Optional[str] = None
    headers: Optional[str] = None


@dataclass
class Domain:
    """A sending domain."""

    domain: str
    status: str
    status_label: str
    can_send: Optional[bool] = None
    cname_status: Optional[str] = None
    dkim_status: Optional[str] = None
    tracking_domain: Optional[str] = None
    dns: Optional[Dict[str, Any]] = None
    dkim: Optional[DkimInfo] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DomainVerification:
    """Domain verification result."""

    domain: str
    dkim_status: str
    cname_status: str
    ownership_verified: Optional[str] = None
    dns: Optional[Dict[str, Any]] = None


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
    event_types: Optional[List[str]] = None
    last_successful_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    last_status: Optional[str] = None


# ---------------------------------------------------------------------------
# Template types
# ---------------------------------------------------------------------------


@dataclass
class MergeTagChild:
    """A child merge tag within a loop block."""

    key: str
    type: Optional[str] = None


@dataclass
class MergeTag:
    """A template merge tag."""

    key: str
    required: bool = False
    type: Optional[str] = None
    children: Optional[List[MergeTagChild]] = None


@dataclass
class Template:
    """An email template."""

    id: int
    name: str
    slug: str
    project_id: int
    folder_id: int
    created_at: str
    updated_at: Optional[str] = None
    active_version: Optional[int] = None
    versions_count: Optional[int] = None
    html: Optional[str] = None
    json: Optional[str] = None
    merge_tags: Optional[List[MergeTag]] = None


@dataclass
class TemplateList:
    """Paginated list of templates."""

    templates: List[Template]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class TemplateMergeTags:
    """Merge tags for a template version."""

    template_slug: str
    version: int
    merge_tags: List[MergeTag]


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
    emoji: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ProjectList:
    """Paginated list of projects."""

    projects: List[Project]
    total: int
    per_page: int
    current_page: int
    last_page: int
