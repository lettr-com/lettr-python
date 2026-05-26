"""Tests for the Audience resource (lists, contacts, topics, properties, segments)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._exceptions import LettrError
from lettr._types import (
    AudienceContact,
    AudienceList,
    AudienceProperty,
    AudienceSegment,
    AudienceTopic,
    BulkContactImportResult,
    BulkDeleteResult,
    BulkListsAttachResult,
    BulkListsDetachResult,
)
from lettr.resources.audience import (
    Audience,
    AudienceContacts,
    AudienceLists,
    AudienceProperties,
    AudienceSegments,
    AudienceTopics,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def audience(mock_client: MagicMock) -> Audience:
    return Audience(mock_client)


@pytest.fixture()
def lists(mock_client: MagicMock) -> AudienceLists:
    return AudienceLists(mock_client)


@pytest.fixture()
def contacts(mock_client: MagicMock) -> AudienceContacts:
    return AudienceContacts(mock_client)


@pytest.fixture()
def topics(mock_client: MagicMock) -> AudienceTopics:
    return AudienceTopics(mock_client)


@pytest.fixture()
def properties(mock_client: MagicMock) -> AudienceProperties:
    return AudienceProperties(mock_client)


@pytest.fixture()
def segments(mock_client: MagicMock) -> AudienceSegments:
    return AudienceSegments(mock_client)


LIST_DATA = {
    "id": "list_1",
    "name": "VIP",
    "contacts_count": 5,
}

CONTACT_DATA = {
    "id": "contact_1",
    "email": "jane@example.com",
    "status": "subscribed",
    "properties": {"first_name": "Jane"},
    "created_at": "2025-01-01T00:00:00Z",
    "lists": [{"id": "list_1", "name": "VIP"}],
    "topics": [{"id": "topic_1", "name": "Updates"}],
}

TOPIC_DATA = {
    "id": "topic_1",
    "name": "Updates",
    "description": "Monthly newsletter",
    "default_subscription": "opt_in",
    "visibility": "public",
    "contacts_count": 12,
    "created_at": "2025-01-01T00:00:00Z",
}

PROPERTY_DATA = {
    "id": "prop_1",
    "name": "first_name",
    "type": "string",
    "fallback_value": "Friend",
    "created_at": "2025-01-01T00:00:00Z",
}

SEGMENT_DATA = {
    "id": "seg_1",
    "name": "Active",
    "list_id": None,
    "list_name": None,
    "condition_groups": [
        {"conditions": [{"field": "status", "operator": "equals", "value": "subscribed"}]}
    ],
    "cached_contacts_count": 3,
    "created_at": "2025-01-01T00:00:00Z",
}

PAGINATION = {"total": 1, "per_page": 25, "current_page": 1, "last_page": 1}


# ---------------------------------------------------------------------------
# Audience container
# ---------------------------------------------------------------------------


class TestAudienceContainer:
    def test_sub_resources_wired(self, audience: Audience) -> None:
        assert isinstance(audience.lists, AudienceLists)
        assert isinstance(audience.contacts, AudienceContacts)
        assert isinstance(audience.topics, AudienceTopics)
        assert isinstance(audience.properties, AudienceProperties)
        assert isinstance(audience.segments, AudienceSegments)


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------


class TestLists:
    def test_list(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"lists": [LIST_DATA], "pagination": PAGINATION}}
        page = lists.list()
        assert len(page.lists) == 1
        assert page.lists[0].name == "VIP"
        assert page.total == 1
        mock_client.get.assert_called_once_with("/audience/lists", params={})

    def test_list_forwards_pagination(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"lists": [], "pagination": PAGINATION}}
        lists.list(per_page=10, page=2)
        params = mock_client.get.call_args.kwargs["params"]
        assert params == {"per_page": 10, "page": 2}

    def test_get(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": LIST_DATA}
        result = lists.get("list_1")
        assert isinstance(result, AudienceList)
        assert result.id == "list_1"
        mock_client.get.assert_called_once_with("/audience/lists/list_1")

    def test_create(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": LIST_DATA}
        result = lists.create(name="VIP")
        assert result.name == "VIP"
        mock_client.post.assert_called_once_with("/audience/lists", json={"name": "VIP"})

    def test_update_partial(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": LIST_DATA}
        lists.update("list_1", name="Renamed")
        mock_client.patch.assert_called_once_with(
            "/audience/lists/list_1", json={"name": "Renamed"}
        )

    def test_update_empty(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": LIST_DATA}
        lists.update("list_1")
        mock_client.patch.assert_called_once_with("/audience/lists/list_1", json={})

    def test_delete(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        lists.delete("list_1")
        mock_client.delete.assert_called_once_with("/audience/lists/list_1")

    def test_bulk_delete(self, lists: AudienceLists, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {"data": {"deleted": 2}}
        result = lists.bulk_delete(list_ids=["list_1", "list_2"])
        assert isinstance(result, BulkDeleteResult)
        assert result.deleted == 2
        mock_client.delete.assert_called_once_with(
            "/audience/lists/bulk",
            json={"list_ids": ["list_1", "list_2"]},
        )

    def test_bulk_delete_empty_body_raises(
        self, lists: AudienceLists, mock_client: MagicMock
    ) -> None:
        """A None body (HTTP 204) becomes a clear LettrError, not TypeError."""
        mock_client.delete.return_value = None
        with pytest.raises(LettrError, match="empty response"):
            lists.bulk_delete(list_ids=["list_1"])


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


class TestContacts:
    def test_list(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {"contacts": [CONTACT_DATA], "pagination": PAGINATION}
        }
        page = contacts.list()
        assert len(page.contacts) == 1
        assert page.contacts[0].email == "jane@example.com"
        assert page.contacts[0].lists[0].name == "VIP"
        assert page.contacts[0].topics[0].id == "topic_1"

    def test_list_forwards_filters(
        self, contacts: AudienceContacts, mock_client: MagicMock
    ) -> None:
        mock_client.get.return_value = {"data": {"contacts": [], "pagination": PAGINATION}}
        contacts.list(
            per_page=50,
            page=3,
            search="jane",
            status="subscribed",
            list_id="list_1",
            segment_id="seg_1",
        )
        params = mock_client.get.call_args.kwargs["params"]
        assert params == {
            "per_page": 50,
            "page": 3,
            "search": "jane",
            "status": "subscribed",
            "list_id": "list_1",
            "segment_id": "seg_1",
        }

    def test_get(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": CONTACT_DATA}
        result = contacts.get("contact_1")
        assert isinstance(result, AudienceContact)
        mock_client.get.assert_called_once_with("/audience/contacts/contact_1")

    def test_create_minimal(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": CONTACT_DATA}
        contacts.create(email="jane@example.com")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload == {"email": "jane@example.com"}

    def test_create_with_all_fields(
        self, contacts: AudienceContacts, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {"data": CONTACT_DATA}
        contacts.create(
            email="jane@example.com",
            list_id="list_1",
            properties={"first_name": "Jane"},
            double_opt_in={
                "from": "no-reply@example.com",
                "subject": "Confirm",
                "template_slug": "doi",
                "redirect_url": "https://example.com/ok",
            },
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["list_id"] == "list_1"
        assert payload["properties"] == {"first_name": "Jane"}
        assert payload["double_opt_in"]["template_slug"] == "doi"

    def test_update_partial(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": CONTACT_DATA}
        contacts.update(
            "contact_1",
            status="unsubscribed",
            properties={"country": "US", "first_name": None},
        )
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload == {
            "status": "unsubscribed",
            "properties": {"country": "US", "first_name": None},
        }
        assert "email" not in payload

    def test_delete(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        contacts.delete("contact_1")
        mock_client.delete.assert_called_once_with("/audience/contacts/contact_1")

    def test_bulk_create(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": {"created": 2, "already_existed": 1}}
        result = contacts.bulk_create(
            emails=["a@example.com", "b@example.com", "c@example.com"],
            list_id="list_1",
        )
        assert isinstance(result, BulkContactImportResult)
        assert result.created == 2
        assert result.already_existed == 1
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload["emails"][0] == "a@example.com"
        assert payload["list_id"] == "list_1"


class TestMemberships:
    def test_add_to_list(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        contacts.add_to_list(contact_id="contact_1", list_id="list_1")
        mock_client.post.assert_called_once_with("/audience/contacts/contact_1/lists/list_1")

    def test_remove_from_list(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        contacts.remove_from_list(contact_id="contact_1", list_id="list_1")
        mock_client.delete.assert_called_once_with("/audience/contacts/contact_1/lists/list_1")

    def test_subscribe_to_topic(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        contacts.subscribe_to_topic(contact_id="contact_1", topic_id="topic_1")
        mock_client.post.assert_called_once_with("/audience/contacts/contact_1/topics/topic_1")

    def test_unsubscribe_from_topic(
        self, contacts: AudienceContacts, mock_client: MagicMock
    ) -> None:
        contacts.unsubscribe_from_topic(contact_id="contact_1", topic_id="topic_1")
        mock_client.delete.assert_called_once_with("/audience/contacts/contact_1/topics/topic_1")

    def test_bulk_attach_lists(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {"attached": 3, "already_attached": 1, "total_pairs": 4}
        }
        result = contacts.bulk_attach_lists(contact_ids=["c1", "c2"], list_ids=["l1", "l2"])
        assert isinstance(result, BulkListsAttachResult)
        assert result.attached == 3
        assert result.total_pairs == 4
        mock_client.post.assert_called_once_with(
            "/audience/contacts/lists/bulk",
            json={"contact_ids": ["c1", "c2"], "list_ids": ["l1", "l2"]},
        )

    def test_bulk_detach_lists(self, contacts: AudienceContacts, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = {
            "data": {"detached": 2, "not_present": 2, "total_pairs": 4}
        }
        result = contacts.bulk_detach_lists(contact_ids=["c1", "c2"], list_ids=["l1", "l2"])
        assert isinstance(result, BulkListsDetachResult)
        assert result.detached == 2
        mock_client.delete.assert_called_once_with(
            "/audience/contacts/lists/bulk",
            json={"contact_ids": ["c1", "c2"], "list_ids": ["l1", "l2"]},
        )


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------


class TestTopics:
    def test_list(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": {"topics": [TOPIC_DATA], "pagination": PAGINATION}}
        page = topics.list()
        assert page.topics[0].visibility == "public"

    def test_get(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": TOPIC_DATA}
        result = topics.get("topic_1")
        assert isinstance(result, AudienceTopic)
        mock_client.get.assert_called_once_with("/audience/topics/topic_1")

    def test_create(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": TOPIC_DATA}
        topics.create(
            name="Updates",
            description="Monthly newsletter",
            default_subscription="opt_in",
            visibility="public",
        )
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload == {
            "name": "Updates",
            "description": "Monthly newsletter",
            "default_subscription": "opt_in",
            "visibility": "public",
        }

    def test_update_partial(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": TOPIC_DATA}
        topics.update("topic_1", name="Renamed")
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload == {"name": "Renamed"}

    def test_update_clear_description(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        """description=None sends `"description": null` to clear the field."""
        mock_client.patch.return_value = {"data": TOPIC_DATA}
        topics.update("topic_1", description=None)
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload == {"description": None}

    def test_update_empty(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        """No args = empty payload (no field is touched, including description)."""
        mock_client.patch.return_value = {"data": TOPIC_DATA}
        topics.update("topic_1")
        mock_client.patch.assert_called_once_with("/audience/topics/topic_1", json={})

    def test_delete(self, topics: AudienceTopics, mock_client: MagicMock) -> None:
        topics.delete("topic_1")
        mock_client.delete.assert_called_once_with("/audience/topics/topic_1")


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestProperties:
    def test_list(self, properties: AudienceProperties, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {"properties": [PROPERTY_DATA], "pagination": PAGINATION}
        }
        page = properties.list()
        assert page.properties[0].name == "first_name"

    def test_get(self, properties: AudienceProperties, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": PROPERTY_DATA}
        result = properties.get("prop_1")
        assert isinstance(result, AudienceProperty)
        mock_client.get.assert_called_once_with("/audience/properties/prop_1")

    def test_create(self, properties: AudienceProperties, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": PROPERTY_DATA}
        properties.create(name="first_name", type="string", fallback_value="Friend")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload == {
            "name": "first_name",
            "type": "string",
            "fallback_value": "Friend",
        }

    def test_update(self, properties: AudienceProperties, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": PROPERTY_DATA}
        properties.update("prop_1", fallback_value="Guest")
        mock_client.patch.assert_called_once_with(
            "/audience/properties/prop_1", json={"fallback_value": "Guest"}
        )

    def test_update_clear_fallback(
        self, properties: AudienceProperties, mock_client: MagicMock
    ) -> None:
        """fallback_value=None sends `"fallback_value": null`."""
        mock_client.patch.return_value = {"data": PROPERTY_DATA}
        properties.update("prop_1", fallback_value=None)
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload == {"fallback_value": None}

    def test_update_empty(self, properties: AudienceProperties, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": PROPERTY_DATA}
        properties.update("prop_1")
        mock_client.patch.assert_called_once_with("/audience/properties/prop_1", json={})

    def test_delete(self, properties: AudienceProperties, mock_client: MagicMock) -> None:
        properties.delete("prop_1")
        mock_client.delete.assert_called_once_with("/audience/properties/prop_1")


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------


class TestSegments:
    def test_list(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {"segments": [SEGMENT_DATA], "pagination": PAGINATION}
        }
        page = segments.list(list_id="list_1")
        assert page.segments[0].name == "Active"
        params = mock_client.get.call_args.kwargs["params"]
        assert params == {"list_id": "list_1"}

    def test_get(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {"data": SEGMENT_DATA}
        result = segments.get("seg_1")
        assert isinstance(result, AudienceSegment)
        assert result.condition_groups[0]["conditions"][0]["field"] == "status"

    def test_create(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {"data": SEGMENT_DATA}
        conditions = {
            "groups": [
                {"conditions": [{"field": "status", "operator": "equals", "value": "subscribed"}]}
            ]
        }
        segments.create(name="Active", conditions=conditions, list_id="list_1")
        payload = mock_client.post.call_args.kwargs["json"]
        assert payload == {
            "name": "Active",
            "conditions": conditions,
            "list_id": "list_1",
        }

    def test_update_partial(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": SEGMENT_DATA}
        segments.update("seg_1", name="Renamed")
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload == {"name": "Renamed"}

    def test_update_clear_list_id(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        """list_id=None sends `"list_id": null` to drop the list restriction."""
        mock_client.patch.return_value = {"data": SEGMENT_DATA}
        segments.update("seg_1", list_id=None)
        payload = mock_client.patch.call_args.kwargs["json"]
        assert payload == {"list_id": None}

    def test_update_empty(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        mock_client.patch.return_value = {"data": SEGMENT_DATA}
        segments.update("seg_1")
        mock_client.patch.assert_called_once_with("/audience/segments/seg_1", json={})

    def test_delete(self, segments: AudienceSegments, mock_client: MagicMock) -> None:
        segments.delete("seg_1")
        mock_client.delete.assert_called_once_with("/audience/segments/seg_1")
