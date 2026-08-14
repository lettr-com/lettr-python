"""Audience management — lists, contacts, topics, properties, segments."""

from __future__ import annotations

import builtins
from typing import Any

from .._client import ApiClient
from .._exceptions import ConflictError, ContactAlreadyExistsError, LettrError
from .._types import (
    UNSET,
    AudienceContact,
    AudienceContactListRef,
    AudienceContactPage,
    AudienceContactTopicRef,
    AudienceList,
    AudienceListPage,
    AudienceProperty,
    AudiencePropertyPage,
    AudienceSegment,
    AudienceSegmentPage,
    AudienceTopic,
    AudienceTopicPage,
    BulkContactError,
    BulkContactImportResult,
    BulkContactRef,
    BulkContactRow,
    BulkDeleteResult,
    BulkListsAttachResult,
    BulkListsDetachResult,
    BulkTopicsSubscribeResult,
    BulkTopicsUnsubscribeResult,
    TopicSubscription,
    _UnsetType,
)

# The only documented 409 on POST /audience/contacts is a duplicate email. Any
# other conflict code the API grows later stays a plain ConflictError.
_RESOURCE_ALREADY_EXISTS = "resource_already_exists"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_body(body: Any, endpoint: str) -> dict[str, Any]:
    """Raise a clear error when a body-returning endpoint responds with no body.

    The HTTP layer returns ``None`` for ``204 No Content``. The audience bulk
    endpoints always respond with ``200`` and a JSON body per the OpenAPI
    spec, so a ``None`` here indicates a server-side regression — surface it
    as a ``LettrError`` rather than letting it become ``TypeError`` further
    down.
    """
    if body is None:
        raise LettrError(f"Unexpected empty response from {endpoint}")
    assert isinstance(body, dict)
    return body


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def _parse_list(d: dict[str, Any]) -> AudienceList:
    return AudienceList(
        id=d["id"],
        name=d["name"],
        contacts_count=d["contacts_count"],
    )


def _parse_contact(d: dict[str, Any]) -> AudienceContact:
    return AudienceContact(
        id=d["id"],
        email=d["email"],
        status=d["status"],
        properties=d.get("properties") or {},
        created_at=d["created_at"],
        lists=[
            AudienceContactListRef(id=item["id"], name=item["name"])
            for item in d.get("lists") or []
        ],
        topics=[
            AudienceContactTopicRef(id=item["id"], name=item["name"])
            for item in d.get("topics") or []
        ],
    )


def _parse_topic(d: dict[str, Any]) -> AudienceTopic:
    return AudienceTopic(
        id=d["id"],
        name=d["name"],
        default_subscription=d["default_subscription"],
        visibility=d["visibility"],
        contacts_count=d["contacts_count"],
        description=d.get("description"),
        created_at=d.get("created_at"),
    )


def _parse_property(d: dict[str, Any]) -> AudienceProperty:
    return AudienceProperty(
        id=d["id"],
        name=d["name"],
        type=d["type"],
        created_at=d["created_at"],
        fallback_value=d.get("fallback_value"),
    )


def _parse_bulk_import(data: dict[str, Any]) -> BulkContactImportResult:
    """Parse a bulk-create body.

    ``updated``, ``error_count``, ``errors`` and ``contacts`` arrived with
    TPL-2105; defaulting them keeps ``result.has_errors`` safe against an API
    deployment that predates the change.
    """
    return BulkContactImportResult(
        created=data["created"],
        already_existed=data["already_existed"],
        updated=data.get("updated", 0),
        error_count=data.get("error_count", 0),
        errors=[
            BulkContactError(
                index=item["index"],
                email=item.get("email"),
                error_code=item["error_code"],
                error=item["error"],
            )
            for item in data.get("errors") or []
        ],
        contacts=[
            BulkContactRef(
                id=item["id"],
                email=item["email"],
                created=item["created"],
            )
            for item in data.get("contacts") or []
        ],
    )


def _parse_segment(d: dict[str, Any]) -> AudienceSegment:
    return AudienceSegment(
        id=d["id"],
        name=d["name"],
        condition_groups=d.get("condition_groups") or [],
        created_at=d["created_at"],
        list_id=d.get("list_id"),
        list_name=d.get("list_name"),
        cached_contacts_count=d.get("cached_contacts_count"),
    )


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------


class AudienceLists:
    """Operations for audience lists.

    Usage::

        page = client.audience.lists.list()
        new = client.audience.lists.create(name="VIP")
        client.audience.lists.delete(new.id)
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        per_page: int | None = None,
        page: int | None = None,
    ) -> AudienceListPage:
        """List audience lists with pagination."""
        params: dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page

        body = self._client.get("/audience/lists", params=params)
        data = body["data"]
        pagination = data["pagination"]
        return AudienceListPage(
            lists=[_parse_list(item) for item in data["lists"]],
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )

    def get(self, list_id: str) -> AudienceList:
        """Get a single audience list by ID."""
        body = self._client.get(f"/audience/lists/{list_id}")
        return _parse_list(body["data"])

    def create(self, *, name: str) -> AudienceList:
        """Create a new audience list."""
        body = self._client.post("/audience/lists", json={"name": name})
        return _parse_list(body["data"])

    def update(self, list_id: str, *, name: str | None = None) -> AudienceList:
        """Update an audience list. Only provided fields are sent."""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        body = self._client.patch(f"/audience/lists/{list_id}", json=payload)
        return _parse_list(body["data"])

    def delete(self, list_id: str) -> None:
        """Delete an audience list."""
        self._client.delete(f"/audience/lists/{list_id}")

    def bulk_delete(self, *, list_ids: builtins.list[str]) -> BulkDeleteResult:
        """Delete multiple audience lists (1–50 IDs)."""
        body = _require_body(
            self._client.delete(
                "/audience/lists/bulk",
                json={"list_ids": list_ids},
            ),
            "DELETE /audience/lists/bulk",
        )
        return BulkDeleteResult(deleted=body["data"]["deleted"])


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


class AudienceContacts:
    """Operations for audience contacts and their list/topic memberships.

    Usage::

        contact = client.audience.contacts.create(email="jane@example.com")
        client.audience.contacts.add_to_list(contact_id=contact.id, list_id="...")
        client.audience.contacts.subscribe_to_topic(contact_id=contact.id, topic_id="...")
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        per_page: int | None = None,
        page: int | None = None,
        search: str | None = None,
        status: str | None = None,
        list_id: str | None = None,
        segment_id: str | None = None,
    ) -> AudienceContactPage:
        """List audience contacts with pagination and filters."""
        params: dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page
        if search is not None:
            params["search"] = search
        if status is not None:
            params["status"] = status
        if list_id is not None:
            params["list_id"] = list_id
        if segment_id is not None:
            params["segment_id"] = segment_id

        body = self._client.get("/audience/contacts", params=params)
        data = body["data"]
        pagination = data["pagination"]
        return AudienceContactPage(
            contacts=[_parse_contact(item) for item in data["contacts"]],
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )

    def get(self, contact_id: str) -> AudienceContact:
        """Get a single contact by ID."""
        body = self._client.get(f"/audience/contacts/{contact_id}")
        return _parse_contact(body["data"])

    def create(
        self,
        *,
        email: str,
        list_id: str | None = None,
        properties: dict[str, str] | None = None,
        double_opt_in: dict[str, Any] | None = None,
    ) -> AudienceContact:
        """Create a single contact.

        Args:
            email: Contact email address.
            list_id: Optional list to add the contact to.
            properties: Custom property values (string).
            double_opt_in: Optional double opt-in config. When provided, the
                contact is created in ``unverified`` status and receives a
                confirmation email. See the API reference for the expected
                shape (``from``, ``subject``, ``template_slug``, ``redirect_url``,
                and optional ``from_name``).

        Raises:
            ContactAlreadyExistsError: The email is already in the team's
                audience. A subclass of ``ConflictError``, so existing handlers
                keep catching it. Do not retry — update the existing contact
                instead, or use ``bulk_create(update_existing=True)``.
        """
        payload: dict[str, Any] = {"email": email}
        if list_id is not None:
            payload["list_id"] = list_id
        if properties is not None:
            payload["properties"] = properties
        if double_opt_in is not None:
            payload["double_opt_in"] = double_opt_in

        try:
            body = self._client.post("/audience/contacts", json=payload)
        except ConflictError as exc:
            if exc.error_code in (None, _RESOURCE_ALREADY_EXISTS):
                raise ContactAlreadyExistsError(
                    message=exc.message,
                    error_code=exc.error_code,
                    email=email,
                ) from exc
            raise

        return _parse_contact(body["data"])

    def update(
        self,
        contact_id: str,
        *,
        email: str | None = None,
        status: str | None = None,
        properties: dict[str, str | None] | None = None,
    ) -> AudienceContact:
        """Update a contact. A property set to ``None`` is removed."""
        payload: dict[str, Any] = {}
        if email is not None:
            payload["email"] = email
        if status is not None:
            payload["status"] = status
        if properties is not None:
            payload["properties"] = properties
        body = self._client.patch(f"/audience/contacts/{contact_id}", json=payload)
        return _parse_contact(body["data"])

    def delete(self, contact_id: str) -> None:
        """Delete a contact."""
        self._client.delete(f"/audience/contacts/{contact_id}")

    def bulk_create(
        self,
        *,
        emails: builtins.list[str] | None = None,
        list_id: str | None = None,
        properties: dict[str, str] | None = None,
        contacts: builtins.list[BulkContactRow] | None = None,
        list_ids: builtins.list[str] | None = None,
        topics: builtins.list[TopicSubscription] | None = None,
        update_existing: bool = False,
    ) -> BulkContactImportResult:
        """Bulk-create up to 1000 contacts.

        Two shapes are supported, and exactly one of them must be filled in:

        - ``emails`` — a flat list of addresses that all share ``list_id`` /
          ``list_ids``, ``properties`` and ``topics``. The original shape,
          unchanged::

              client.audience.contacts.bulk_create(
                  emails=["a@example.com", "b@example.com"],
                  list_id="01h-everyone",
              )

        - ``contacts`` — one :class:`~lettr.BulkContactRow` per contact, each
          with its own properties, lists and topic subscriptions::

              client.audience.contacts.bulk_create(
                  contacts=[
                      BulkContactRow(email="cara@example.com", properties={"plan": "pro"}),
                      BulkContactRow(
                          email="dan@example.com",
                          topics=[TopicSubscription.opt_out("01h-promos")],
                      ),
                  ],
                  list_ids=["01h-everyone"],
              )

        Batch-wide ``list_ids`` and ``topics`` are unioned into every row; a
        row-level property key or ``opt_out`` wins over the batch-wide value.

        Args:
            emails: 1–1000 addresses. Alternative to ``contacts``.
            list_id: Single batch-wide list. Folded into ``list_ids`` server-side.
            properties: Applied to every contact in the batch; a row's own key wins.
            contacts: 1–1000 rows. Alternative to ``emails``.
            list_ids: Max 50 batch-wide lists.
            topics: Max 50 batch-wide topic subscriptions.
            update_existing: When ``True``, existing contacts have their
                properties merged (submitted keys overwrite, absent keys are
                preserved) and ``opt_out`` entries applied. When ``False`` (the
                default) existing contacts keep their properties but are still
                attached to the requested lists.

        Returns:
            A :class:`~lettr.BulkContactImportResult`. Rows that fail validation
            are skipped rather than failing the request: the call still returns
            HTTP 201 and reports them in ``errors``. Check ``result.has_errors``
            — a call that does not raise does not mean every row landed.

        Raises:
            ValueError: Neither ``emails`` nor ``contacts`` was provided.
        """
        if not emails and not contacts:
            raise ValueError(
                "bulk_create() needs at least one entry in either emails or contacts."
            )

        payload: dict[str, Any] = {}
        if emails:
            payload["emails"] = list(emails)
        if list_id is not None:
            payload["list_id"] = list_id
        if properties is not None:
            payload["properties"] = properties
        if contacts is not None:
            payload["contacts"] = [row.to_payload() for row in contacts]
        if list_ids is not None:
            payload["list_ids"] = list(list_ids)
        if topics is not None:
            payload["topics"] = [topic.to_payload() for topic in topics]
        # Omitted when False so a legacy payload stays byte-identical; the API
        # defaults it to False anyway.
        if update_existing:
            payload["update_existing"] = True

        body = self._client.post("/audience/contacts/bulk", json=payload)
        return _parse_bulk_import(body["data"])

    # -- list memberships ---------------------------------------------------

    def add_to_list(self, *, contact_id: str, list_id: str) -> None:
        """Attach a contact to a list (idempotent)."""
        self._client.post(f"/audience/contacts/{contact_id}/lists/{list_id}")

    def remove_from_list(self, *, contact_id: str, list_id: str) -> None:
        """Detach a contact from a list (idempotent)."""
        self._client.delete(f"/audience/contacts/{contact_id}/lists/{list_id}")

    def bulk_attach_lists(
        self,
        *,
        contact_ids: builtins.list[str],
        list_ids: builtins.list[str],
    ) -> BulkListsAttachResult:
        """Attach all ``contact_ids`` × ``list_ids`` pairs."""
        body = _require_body(
            self._client.post(
                "/audience/contacts/lists/bulk",
                json={"contact_ids": contact_ids, "list_ids": list_ids},
            ),
            "POST /audience/contacts/lists/bulk",
        )
        data = body["data"]
        return BulkListsAttachResult(
            attached=data["attached"],
            already_attached=data["already_attached"],
            total_pairs=data["total_pairs"],
        )

    def bulk_detach_lists(
        self,
        *,
        contact_ids: builtins.list[str],
        list_ids: builtins.list[str],
    ) -> BulkListsDetachResult:
        """Detach all ``contact_ids`` × ``list_ids`` pairs."""
        body = _require_body(
            self._client.delete(
                "/audience/contacts/lists/bulk",
                json={"contact_ids": contact_ids, "list_ids": list_ids},
            ),
            "DELETE /audience/contacts/lists/bulk",
        )
        data = body["data"]
        return BulkListsDetachResult(
            detached=data["detached"],
            not_present=data["not_present"],
            total_pairs=data["total_pairs"],
        )

    # -- topic subscriptions ------------------------------------------------

    def subscribe_to_topic(self, *, contact_id: str, topic_id: str) -> None:
        """Subscribe a contact to a topic (idempotent)."""
        self._client.post(f"/audience/contacts/{contact_id}/topics/{topic_id}")

    def unsubscribe_from_topic(self, *, contact_id: str, topic_id: str) -> None:
        """Unsubscribe a contact from a topic (idempotent)."""
        self._client.delete(f"/audience/contacts/{contact_id}/topics/{topic_id}")

    def bulk_subscribe_topics(
        self,
        *,
        contact_ids: builtins.list[str],
        topic_ids: builtins.list[str],
    ) -> BulkTopicsSubscribeResult:
        """Subscribe all ``contact_ids`` × ``topic_ids`` pairs (up to 1000 × 50).

        Feed it ``result.contact_ids`` from a ``bulk_create()`` — no id lookup
        needed.
        """
        body = _require_body(
            self._client.post(
                "/audience/contacts/topics/bulk",
                json={"contact_ids": contact_ids, "topic_ids": topic_ids},
            ),
            "POST /audience/contacts/topics/bulk",
        )
        data = body["data"]
        return BulkTopicsSubscribeResult(
            subscribed=data["subscribed"],
            already_subscribed=data["already_subscribed"],
            total_pairs=data["total_pairs"],
        )

    def bulk_unsubscribe_topics(
        self,
        *,
        contact_ids: builtins.list[str],
        topic_ids: builtins.list[str],
    ) -> BulkTopicsUnsubscribeResult:
        """Unsubscribe all ``contact_ids`` × ``topic_ids`` pairs.

        Pairs that do not exist are ignored. Note this is a ``DELETE`` carrying
        a request body — ``httpx`` handles that, as it already does for
        ``bulk_detach_lists()``.
        """
        body = _require_body(
            self._client.delete(
                "/audience/contacts/topics/bulk",
                json={"contact_ids": contact_ids, "topic_ids": topic_ids},
            ),
            "DELETE /audience/contacts/topics/bulk",
        )
        data = body["data"]
        return BulkTopicsUnsubscribeResult(
            unsubscribed=data["unsubscribed"],
            total_pairs=data["total_pairs"],
        )


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


class AudienceTopics:
    """Operations for audience topics."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        per_page: int | None = None,
        page: int | None = None,
    ) -> AudienceTopicPage:
        """List audience topics with pagination."""
        params: dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page
        body = self._client.get("/audience/topics", params=params)
        data = body["data"]
        pagination = data["pagination"]
        return AudienceTopicPage(
            topics=[_parse_topic(item) for item in data["topics"]],
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )

    def get(self, topic_id: str) -> AudienceTopic:
        """Get a single topic by ID."""
        body = self._client.get(f"/audience/topics/{topic_id}")
        return _parse_topic(body["data"])

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        default_subscription: str | None = None,
        visibility: str | None = None,
    ) -> AudienceTopic:
        """Create a new topic.

        Args:
            name: Topic name.
            description: Optional description.
            default_subscription: ``"opt_in"`` or ``"opt_out"`` (immutable
                after creation; defaults to ``opt_in`` on the server).
            visibility: ``"private"`` or ``"public"`` (defaults to
                ``private`` on the server).
        """
        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description"] = description
        if default_subscription is not None:
            payload["default_subscription"] = default_subscription
        if visibility is not None:
            payload["visibility"] = visibility
        body = self._client.post("/audience/topics", json=payload)
        return _parse_topic(body["data"])

    def update(
        self,
        topic_id: str,
        *,
        name: str | _UnsetType = UNSET,
        description: str | None | _UnsetType = UNSET,
        visibility: str | _UnsetType = UNSET,
    ) -> AudienceTopic:
        """Update a topic. ``default_subscription`` is immutable.

        Pass ``description=None`` to clear the description; omit the
        argument to leave it unchanged.
        """
        payload: dict[str, Any] = {}
        if not isinstance(name, _UnsetType):
            payload["name"] = name
        if not isinstance(description, _UnsetType):
            payload["description"] = description
        if not isinstance(visibility, _UnsetType):
            payload["visibility"] = visibility
        body = self._client.patch(f"/audience/topics/{topic_id}", json=payload)
        return _parse_topic(body["data"])

    def delete(self, topic_id: str) -> None:
        """Delete a topic."""
        self._client.delete(f"/audience/topics/{topic_id}")


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class AudienceProperties:
    """Operations for audience custom property definitions."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        per_page: int | None = None,
        page: int | None = None,
    ) -> AudiencePropertyPage:
        """List audience properties with pagination."""
        params: dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page
        body = self._client.get("/audience/properties", params=params)
        data = body["data"]
        pagination = data["pagination"]
        return AudiencePropertyPage(
            properties=[_parse_property(item) for item in data["properties"]],
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )

    def get(self, property_id: str) -> AudienceProperty:
        """Get a single property by ID."""
        body = self._client.get(f"/audience/properties/{property_id}")
        return _parse_property(body["data"])

    def create(
        self,
        *,
        name: str,
        type: str,
        fallback_value: str | None = None,
    ) -> AudienceProperty:
        """Create a property definition.

        Args:
            name: Property name (lowercase letters, digits, underscores;
                must start with a letter).
            type: One of ``"string"``, ``"number"``, ``"boolean"``,
                ``"date"``, ``"json"``.
            fallback_value: Optional fallback used when a contact has no
                value for this property.
        """
        payload: dict[str, Any] = {"name": name, "type": type}
        if fallback_value is not None:
            payload["fallback_value"] = fallback_value
        body = self._client.post("/audience/properties", json=payload)
        return _parse_property(body["data"])

    def update(
        self,
        property_id: str,
        *,
        fallback_value: str | None | _UnsetType = UNSET,
    ) -> AudienceProperty:
        """Update a property's ``fallback_value``. ``name`` and ``type`` are
        immutable.

        Pass ``fallback_value=None`` to clear the fallback; omit the
        argument to leave it unchanged.
        """
        payload: dict[str, Any] = {}
        if not isinstance(fallback_value, _UnsetType):
            payload["fallback_value"] = fallback_value
        body = self._client.patch(f"/audience/properties/{property_id}", json=payload)
        return _parse_property(body["data"])

    def delete(self, property_id: str) -> None:
        """Delete a property."""
        self._client.delete(f"/audience/properties/{property_id}")


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------


class AudienceSegments:
    """Operations for audience segments."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(
        self,
        *,
        per_page: int | None = None,
        page: int | None = None,
        list_id: str | None = None,
    ) -> AudienceSegmentPage:
        """List audience segments with pagination."""
        params: dict[str, Any] = {}
        if per_page is not None:
            params["per_page"] = per_page
        if page is not None:
            params["page"] = page
        if list_id is not None:
            params["list_id"] = list_id
        body = self._client.get("/audience/segments", params=params)
        data = body["data"]
        pagination = data["pagination"]
        return AudienceSegmentPage(
            segments=[_parse_segment(item) for item in data["segments"]],
            total=pagination["total"],
            per_page=pagination["per_page"],
            current_page=pagination["current_page"],
            last_page=pagination["last_page"],
        )

    def get(self, segment_id: str) -> AudienceSegment:
        """Get a single segment by ID."""
        body = self._client.get(f"/audience/segments/{segment_id}")
        return _parse_segment(body["data"])

    def create(
        self,
        *,
        name: str,
        conditions: dict[str, Any],
        list_id: str | None = None,
    ) -> AudienceSegment:
        """Create a segment.

        Args:
            name: Segment name.
            conditions: Raw condition object matching the OpenAPI
                ``SegmentConditionsInput`` shape, e.g.::

                    {"groups": [{"conditions": [
                        {"field": "email", "operator": "contains",
                         "value": "@example.com"}
                    ]}]}
            list_id: Optional list to restrict the segment to.
        """
        payload: dict[str, Any] = {"name": name, "conditions": conditions}
        if list_id is not None:
            payload["list_id"] = list_id
        body = self._client.post("/audience/segments", json=payload)
        return _parse_segment(body["data"])

    def update(
        self,
        segment_id: str,
        *,
        name: str | _UnsetType = UNSET,
        conditions: dict[str, Any] | _UnsetType = UNSET,
        list_id: str | None | _UnsetType = UNSET,
    ) -> AudienceSegment:
        """Update a segment. Only provided fields are sent.

        Pass ``list_id=None`` to clear the list restriction (segment applies
        to all lists); omit the argument to leave it unchanged.
        """
        payload: dict[str, Any] = {}
        if not isinstance(name, _UnsetType):
            payload["name"] = name
        if not isinstance(conditions, _UnsetType):
            payload["conditions"] = conditions
        if not isinstance(list_id, _UnsetType):
            payload["list_id"] = list_id
        body = self._client.patch(f"/audience/segments/{segment_id}", json=payload)
        return _parse_segment(body["data"])

    def delete(self, segment_id: str) -> None:
        """Delete a segment."""
        self._client.delete(f"/audience/segments/{segment_id}")


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------


class Audience:
    """Audience management — entry point for lists, contacts, topics,
    properties, and segments.

    Usage::

        client.audience.lists.list()
        client.audience.contacts.create(email="jane@example.com")
        client.audience.topics.list()
        client.audience.properties.create(name="first_name", type="string")
        client.audience.segments.create(name="Active", conditions={...})
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client
        self.lists = AudienceLists(client)
        self.contacts = AudienceContacts(client)
        self.topics = AudienceTopics(client)
        self.properties = AudienceProperties(client)
        self.segments = AudienceSegments(client)
