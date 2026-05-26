"""Audience management — lists, contacts, topics, properties, segments."""

from __future__ import annotations

import builtins
from typing import Any

from .._client import ApiClient
from .._exceptions import LettrError
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
    BulkContactImportResult,
    BulkDeleteResult,
    BulkListsAttachResult,
    BulkListsDetachResult,
    _UnsetType,
)

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
        """
        payload: dict[str, Any] = {"email": email}
        if list_id is not None:
            payload["list_id"] = list_id
        if properties is not None:
            payload["properties"] = properties
        if double_opt_in is not None:
            payload["double_opt_in"] = double_opt_in
        body = self._client.post("/audience/contacts", json=payload)
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
        emails: builtins.list[str],
        list_id: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> BulkContactImportResult:
        """Bulk-create up to 1000 contacts."""
        payload: dict[str, Any] = {"emails": emails}
        if list_id is not None:
            payload["list_id"] = list_id
        if properties is not None:
            payload["properties"] = properties
        body = self._client.post("/audience/contacts/bulk", json=payload)
        data = body["data"]
        return BulkContactImportResult(
            created=data["created"],
            already_existed=data["already_existed"],
        )

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
