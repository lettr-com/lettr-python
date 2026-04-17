"""Tests for the Domains resource."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from lettr._types import Domain, DomainDnsVerification, DomainVerification
from lettr.resources.domains import Domains


@pytest.fixture()
def domains(mock_client: MagicMock) -> Domains:
    return Domains(mock_client)


class TestList:
    def test_list_domains(self, domains: Domains, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "domains": [
                    {
                        "domain": "example.com",
                        "status": "verified",
                        "status_label": "Verified",
                        "can_send": True,
                        "cname_status": "valid",
                        "dkim_status": "valid",
                        "created_at": "2025-01-01",
                        "updated_at": "2025-06-01",
                    }
                ]
            }
        }

        result = domains.list()
        assert len(result) == 1
        assert isinstance(result[0], Domain)
        assert result[0].domain == "example.com"
        assert result[0].can_send is True


class TestGet:
    def test_get_domain(self, domains: Domains, mock_client: MagicMock) -> None:
        mock_client.get.return_value = {
            "data": {
                "domain": "example.com",
                "status": "verified",
                "status_label": "Verified",
                "can_send": True,
                "cname_status": "valid",
                "dkim_status": "valid",
                "dmarc_status": "valid",
                "spf_status": "valid",
                "is_primary_domain": True,
                "tracking_domain": "track.example.com",
                "dns": {"cname": "cname.lettr.com"},
                "dns_provider": {
                    "provider": "cloudflare",
                    "provider_label": "Cloudflare",
                    "nameservers": ["ns1.cloudflare.com", "ns2.cloudflare.com"],
                    "error": None,
                },
                "created_at": "2025-01-01",
                "updated_at": "2025-06-01",
            }
        }

        result = domains.get("example.com")
        assert isinstance(result, Domain)
        assert result.dmarc_status == "valid"
        assert result.spf_status == "valid"
        assert result.is_primary_domain is True
        assert result.dns_provider is not None
        assert result.dns_provider.provider == "cloudflare"
        assert result.dns_provider.provider_label == "Cloudflare"


class TestCreate:
    def test_create_domain(self, domains: Domains, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {
                "domain": "new.com",
                "status": "pending",
                "status_label": "Pending",
                "dkim": {
                    "public": "MIGfMA0...",
                    "selector": "lettr",
                    "headers": "from:to:subject",
                    "signing_domain": "new.com",
                },
            }
        }

        result = domains.create("new.com")
        assert result.domain == "new.com"
        assert result.status == "pending"
        assert result.dkim is not None
        assert result.dkim.selector == "lettr"
        assert result.dkim.signing_domain == "new.com"

        payload = mock_client.post.call_args.kwargs["json"]
        assert payload == {"domain": "new.com"}

    def test_create_domain_tolerates_unknown_dkim_fields(
        self, domains: Domains, mock_client: MagicMock
    ) -> None:
        """Regression: unknown server fields must not crash dataclass parsing."""
        mock_client.post.return_value = {
            "data": {
                "domain": "new.com",
                "status": "pending",
                "status_label": "Pending",
                "dkim": {
                    "selector": "lettr",
                    "headers": "from:to:subject",
                    "signing_domain": "new.com",
                    "future_field_we_dont_know_about": "some_value",
                    "another_one": 42,
                },
            }
        }

        result = domains.create("new.com")
        assert result.dkim is not None
        assert result.dkim.selector == "lettr"


class TestDelete:
    def test_delete_domain(self, domains: Domains, mock_client: MagicMock) -> None:
        mock_client.delete.return_value = None
        domains.delete("example.com")
        mock_client.delete.assert_called_once_with("/domains/example.com")


class TestVerify:
    def test_verify_domain(self, domains: Domains, mock_client: MagicMock) -> None:
        mock_client.post.return_value = {
            "data": {
                "domain": "example.com",
                "dkim_status": "valid",
                "cname_status": "valid",
                "dmarc_status": "valid",
                "spf_status": "valid",
                "is_primary_domain": True,
                "ownership_verified": "2025-01-01",
                "dns": {
                    "dkim_record": "v=DKIM1; k=rsa; p=MIGfMA0...",
                    "cname_record": "example.com.d.]sparkpostmail.com",
                    "dkim_error": None,
                    "cname_error": None,
                },
                "dmarc": {
                    "is_valid": True,
                    "status": "valid",
                    "record": "v=DMARC1; p=reject",
                    "policy": "reject",
                },
                "spf": {
                    "is_valid": True,
                    "status": "valid",
                    "record": "v=spf1 include:lettr.com ~all",
                    "includes_sparkpost": True,
                },
            }
        }

        result = domains.verify("example.com")
        assert isinstance(result, DomainVerification)
        assert result.dmarc_status == "valid"
        assert result.spf_status == "valid"
        assert result.is_primary_domain is True
        assert result.dmarc is not None
        assert result.dmarc.policy == "reject"
        assert result.spf is not None
        assert result.spf.includes_sparkpost is True
        assert isinstance(result.dns, DomainDnsVerification)
        assert result.dns.dkim_record == "v=DKIM1; k=rsa; p=MIGfMA0..."
        assert result.dns.cname_error is None

    def test_verify_without_dmarc_spf_objects(
        self, domains: Domains, mock_client: MagicMock
    ) -> None:
        mock_client.post.return_value = {
            "data": {
                "domain": "example.com",
                "dkim_status": "pending",
                "cname_status": "pending",
                "dmarc_status": "unverified",
                "spf_status": "unverified",
                "is_primary_domain": False,
            }
        }

        result = domains.verify("example.com")
        assert result.dmarc is None
        assert result.spf is None
        assert result.dmarc_status == "unverified"
        assert result.spf_status == "unverified"
        assert result.is_primary_domain is False
