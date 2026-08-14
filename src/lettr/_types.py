"""Type definitions for the Lettr SDK."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Final, Literal, TypeVar

T = TypeVar("T")


class _UnsetType:
    """Sentinel type for fields that were not provided.

    Used by update methods to distinguish "field not provided" (the default)
    from "set to null". Do not instantiate — use the singleton :data:`UNSET`.
    """

    _instance: _UnsetType | None = None

    def __new__(cls) -> _UnsetType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Final[_UnsetType] = _UnsetType()
"""Sentinel meaning "field not provided".

Pass to an update method's keyword to leave the field unchanged, or pass
``None`` to explicitly clear a nullable field. Importing::

    from lettr import UNSET
"""


def _from_dict(cls: type[T], data: dict[str, Any]) -> T:
    """Build a dataclass instance from a dict, ignoring unknown keys.

    Server payloads may add new fields over time; using bare ``cls(**data)``
    crashes on the first unknown key. This helper filters ``data`` to only
    the fields declared on ``cls`` so that forward-compatible parsing works.
    """
    known = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    return cls(**{k: v for k, v in data.items() if k in known})


def _pagination_kwargs(p: dict[str, Any]) -> dict[str, int]:
    """Extract the standard four-field page-based pagination kwargs.

    The Laravel-style paginator returns ``{total, per_page, current_page,
    last_page}`` on every list endpoint. Helper exists so each ``*Page``
    parser unpacks the same four keys consistently rather than spelling them
    out by hand.
    """
    return {
        "total": p["total"],
        "per_page": p["per_page"],
        "current_page": p["current_page"],
        "last_page": p["last_page"],
    }


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
    bounce_class: int | None = None
    queue_time: int | None = None
    outbound_tls: str | None = None
    num_retries: int | None = None
    device_token: str | None = None
    target_link_url: str | None = None
    target_link_name: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None
    initial_pixel: bool | None = None
    fbtype: str | None = None
    report_by: str | None = None
    report_to: str | None = None
    remote_addr: str | None = None
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
class DnsProvider:
    """DNS provider information for a domain."""

    provider: str | None = None
    provider_label: str | None = None
    nameservers: list[str] | None = None
    error: str | None = None


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
    dns_provider: DnsProvider | None = None
    dkim: DkimInfo | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class DomainDnsVerification:
    """DNS verification error details for a domain."""

    dkim_record: str | None = None
    cname_record: str | None = None
    dkim_error: str | None = None
    cname_error: str | None = None
    dmarc_record: str | None = None
    dmarc_error: str | None = None
    spf_record: str | None = None
    spf_error: str | None = None


@dataclass
class DomainVerification:
    """Domain verification result."""

    domain: str
    dkim_status: str
    cname_status: str
    dmarc_status: str
    spf_status: str
    is_primary_domain: bool
    ownership_verified: str | None = None
    dns: DomainDnsVerification | None = None
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
    name: str | None = None
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


@dataclass
class TemplateHtml:
    """Response from the get template HTML endpoint."""

    html: str
    merge_tags: list[MergeTag] | None = None
    subject: str | None = None


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


# ---------------------------------------------------------------------------
# Audience types
# ---------------------------------------------------------------------------


@dataclass
class AudienceList:
    """An audience list."""

    id: str
    name: str
    contacts_count: int


@dataclass
class AudienceListPage:
    """Paginated list of audience lists."""

    lists: list[AudienceList]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class AudienceContactListRef:
    """A list reference embedded in a contact."""

    id: str
    name: str


@dataclass
class AudienceContactTopicRef:
    """A topic reference embedded in a contact."""

    id: str
    name: str


@dataclass
class AudienceContact:
    """An audience contact."""

    id: str
    email: str
    status: str
    properties: dict[str, str]
    created_at: str
    lists: list[AudienceContactListRef]
    topics: list[AudienceContactTopicRef]


@dataclass
class AudienceContactPage:
    """Paginated list of audience contacts."""

    contacts: list[AudienceContact]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class AudienceTopic:
    """An audience topic."""

    id: str
    name: str
    default_subscription: str
    visibility: str
    contacts_count: int
    description: str | None = None
    created_at: str | None = None


@dataclass
class AudienceTopicPage:
    """Paginated list of audience topics."""

    topics: list[AudienceTopic]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class AudienceProperty:
    """An audience custom property definition."""

    id: str
    name: str
    type: str
    created_at: str
    fallback_value: str | None = None


@dataclass
class AudiencePropertyPage:
    """Paginated list of audience properties."""

    properties: list[AudienceProperty]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class AudienceSegment:
    """An audience segment.

    ``condition_groups`` is kept as a list of raw dicts mirroring the
    API shape (groups joined by OR, conditions within a group joined by AND).
    """

    id: str
    name: str
    condition_groups: list[dict[str, Any]]
    created_at: str
    list_id: str | None = None
    list_name: str | None = None
    cached_contacts_count: int | None = None


@dataclass
class AudienceSegmentPage:
    """Paginated list of audience segments."""

    segments: list[AudienceSegment]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class BulkDeleteResult:
    """Result of a bulk delete operation."""

    deleted: int


TopicSubscriptionState = Literal["opt_in", "opt_out"]
"""What a write request should *do* with a topic.

Distinct from a topic's ``default_subscription``, which describes how the topic
behaves for a contact that says nothing. ``"opt_out"`` here also cancels the
auto-subscription a topic with ``default_subscription="opt_out"`` would
otherwise give a newly created contact, so a create and an unsubscribe fit in
one request.
"""

BulkContactErrorCode = Literal[
    "missing_email",
    "invalid_email",
    "invalid_property_value",
    "unknown_property_key",
    "unknown_list",
    "unknown_topic",
    "invalid_topic_subscription",
]
"""Reason a single row was skipped during a bulk create.

Per-row codes reported inside a ``201`` body — not the top-level ``error_code``
of a failed request.
"""


@dataclass
class TopicSubscription:
    """A topic and the subscription state to apply to it.

    Used batch-wide on :meth:`~lettr.resources.audience.AudienceContacts.bulk_create`
    and per row on :class:`BulkContactRow`. A row-level ``opt_out`` wins over a
    batch-level ``opt_in`` for that contact.

    Build them with the constructors for readability at the call site::

        TopicSubscription.opt_in("01h-newsletter")
        TopicSubscription.opt_out("01h-promos")
    """

    id: str
    subscription: TopicSubscriptionState = "opt_in"

    @classmethod
    def opt_in(cls, topic_id: str) -> TopicSubscription:
        """Subscribe the contact to the topic."""
        return cls(id=topic_id, subscription="opt_in")

    @classmethod
    def opt_out(cls, topic_id: str) -> TopicSubscription:
        """Suppress the topic for the contact.

        Including a topic that would otherwise auto-subscribe newly created
        contacts.
        """
        return cls(id=topic_id, subscription="opt_out")

    def to_payload(self) -> dict[str, Any]:
        return {"id": self.id, "subscription": self.subscription}


@dataclass
class BulkContactRow:
    """One contact in a bulk create payload.

    ``list_ids`` and ``topics`` here are applied **on top of** the batch-wide
    ones passed to ``bulk_create()``; a ``properties`` key here overrides the
    batch-wide value for the same key.

    A row that fails validation is skipped rather than failing the request — it
    comes back in :attr:`BulkContactImportResult.errors`.
    """

    email: str
    properties: dict[str, str] | None = None
    """Each key must match a property defined for the team."""

    list_ids: list[str] | None = None
    topics: list[TopicSubscription] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"email": self.email}
        if self.properties is not None:
            payload["properties"] = self.properties
        if self.list_ids is not None:
            payload["list_ids"] = list(self.list_ids)
        if self.topics is not None:
            payload["topics"] = [topic.to_payload() for topic in self.topics]
        return payload


@dataclass
class BulkContactError:
    """A row that was skipped during a bulk create."""

    index: int
    """Zero-based position of the row in the submitted sequence."""

    email: str | None
    error_code: BulkContactErrorCode | str
    """Typed as a union so a code added server-side survives as a plain string."""

    error: str


@dataclass
class BulkContactRef:
    """Identity of a contact that exists after a bulk create.

    Lets a caller chain into the bulk list and topic endpoints without a
    follow-up lookup.
    """

    id: str
    email: str
    created: bool
    """``True`` when this request created the contact, ``False`` when it already existed."""


@dataclass
class BulkContactImportResult:
    """Result of bulk-creating contacts.

    A bulk create can **partially succeed**: rows that fail validation are
    skipped and reported in :attr:`errors` while the rest of the batch is
    written, and the call still returns HTTP 201. A call that does not raise
    therefore does not mean every row landed — check :attr:`has_errors`.

    :attr:`already_existed` and :attr:`updated` overlap by design. They answer
    different questions ("was the address already in the audience?" vs "did this
    request change the contact?"), so they do not sum to the row count: a
    contact that already existed and got attached to a list is counted in both.
    """

    created: int
    already_existed: int
    updated: int = 0
    """Existing contacts this request changed — properties merged, a list or
    topic attached, or a subscription dropped."""

    error_count: int = 0
    """Number of skipped rows."""

    errors: list[BulkContactError] = field(default_factory=list)
    contacts: list[BulkContactRef] = field(default_factory=list)
    """Every contact that exists after the request, in submission order."""

    @property
    def has_errors(self) -> bool:
        """Whether any row was skipped.

        Always check this — a bulk create reports partial failures in the body,
        not in the HTTP status.
        """
        return bool(self.errors)

    @property
    def contact_ids(self) -> list[str]:
        """Ids of every contact that exists after the request, in submission order.

        Ready to feed into ``bulk_attach_lists()`` or ``bulk_subscribe_topics()``.
        """
        return [contact.id for contact in self.contacts]

    def id_for(self, email: str) -> str | None:
        """Look up the id for a submitted address.

        Matching is case-insensitive because the API normalizes addresses
        before storing them.
        """
        needle = email.strip().lower()
        for contact in self.contacts:
            if contact.email.lower() == needle:
                return contact.id
        return None


@dataclass
class BulkTopicsSubscribeResult:
    """Result of bulk-subscribing contacts to topics."""

    subscribed: int
    already_subscribed: int
    total_pairs: int


@dataclass
class BulkTopicsUnsubscribeResult:
    """Result of bulk-unsubscribing contacts from topics."""

    unsubscribed: int
    total_pairs: int


@dataclass
class BulkListsAttachResult:
    """Result of bulk-attaching contacts to lists."""

    attached: int
    already_attached: int
    total_pairs: int


@dataclass
class BulkListsDetachResult:
    """Result of bulk-detaching contacts from lists."""

    detached: int
    not_present: int
    total_pairs: int


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------


@dataclass
class CampaignStats:
    """Aggregated engagement statistics for a campaign."""

    injections: int
    deliveries: int
    bounces: int
    spam_complaints: int
    opens: int
    unique_opens: int
    clicks: int
    unique_clicks: int
    unsubscribes: int


@dataclass
class Campaign:
    """A campaign with embedded engagement stats.

    Returned by :meth:`Campaigns.list`, :meth:`Campaigns.send`,
    :meth:`Campaigns.schedule`, and :meth:`Campaigns.unschedule`. The
    rendered email body lives on :class:`CampaignDetail` (returned by
    :meth:`Campaigns.get`) so callers of the list/action endpoints aren't
    handed an attribute that the API never populates there.
    """

    id: str
    name: str
    status: str
    sent_count: int
    created_at: str
    stats: CampaignStats
    subject: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    scheduled_at: str | None = None
    total_recipients: int | None = None
    sent_at: str | None = None


@dataclass
class CampaignDetail(Campaign):
    """A campaign plus its rendered HTML body.

    Returned only by :meth:`Campaigns.get`. Inherits every :class:`Campaign`
    field so existing summary-shaped consumers keep working unchanged.
    """

    html_content: str | None = None


@dataclass
class CampaignPage:
    """Paginated list of campaigns."""

    campaigns: list[Campaign]
    total: int
    per_page: int
    current_page: int
    last_page: int


@dataclass
class CampaignEvent:
    """A single campaign engagement event."""

    event_id: str
    event_type: str
    email: str
    timestamp: str
    bounce_class: str | None = None
    reason: str | None = None
    target_link_url: str | None = None
    user_agent: str | None = None


@dataclass
class CampaignEventPage:
    """Cursor-paginated list of campaign events."""

    events: list[CampaignEvent]
    next_cursor: str | None = None
