"""Domain management."""

from __future__ import annotations

from typing import List

from .._client import ApiClient
from .._types import DkimInfo, Domain, DomainVerification


class Domains:
    """Operations for managing sending domains.

    Usage::

        domains = client.domains.list()
        domain = client.domains.create("example.com")
        verification = client.domains.verify("example.com")
    """

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    def list(self) -> List[Domain]:
        """List all sending domains.

        Returns:
            A list of :class:`Domain` objects.
        """
        body = self._client.get("/domains")
        return [
            Domain(
                domain=d["domain"],
                status=d["status"],
                status_label=d["status_label"],
                can_send=d.get("can_send"),
                cname_status=d.get("cname_status"),
                dkim_status=d.get("dkim_status"),
                created_at=d.get("created_at"),
                updated_at=d.get("updated_at"),
            )
            for d in body["data"]["domains"]
        ]

    def get(self, domain: str) -> Domain:
        """Get details of a single sending domain.

        Args:
            domain: The domain name (e.g. ``"example.com"``).

        Returns:
            A :class:`Domain` with full details including DNS records.

        Raises:
            NotFoundError: If the domain is not found.
        """
        body = self._client.get(f"/domains/{domain}")
        d = body["data"]
        return Domain(
            domain=d["domain"],
            status=d["status"],
            status_label=d["status_label"],
            can_send=d.get("can_send"),
            cname_status=d.get("cname_status"),
            dkim_status=d.get("dkim_status"),
            tracking_domain=d.get("tracking_domain"),
            dns=d.get("dns"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )

    def create(self, domain: str) -> Domain:
        """Register a new sending domain.

        The domain will be created in a pending state until DNS records are
        verified and the domain is approved.

        Args:
            domain: The domain name to register (e.g. ``"example.com"``).

        Returns:
            A :class:`Domain` with DKIM configuration for DNS setup.

        Raises:
            ConflictError: If the domain already exists.
            ValidationError: If the domain format is invalid.
        """
        body = self._client.post("/domains", json={"domain": domain})
        d = body["data"]
        dkim = None
        if d.get("dkim"):
            dkim = DkimInfo(**d["dkim"])
        return Domain(
            domain=d["domain"],
            status=d["status"],
            status_label=d["status_label"],
            dkim=dkim,
        )

    def delete(self, domain: str) -> None:
        """Delete a sending domain.

        Args:
            domain: The domain name to delete.

        Raises:
            NotFoundError: If the domain is not found.
        """
        self._client.delete(f"/domains/{domain}")

    def verify(self, domain: str) -> DomainVerification:
        """Verify a domain's DNS records (DKIM and CNAME).

        Args:
            domain: The domain name to verify.

        Returns:
            A :class:`DomainVerification` with the current DNS status.

        Raises:
            NotFoundError: If the domain is not found.
        """
        body = self._client.post(f"/domains/{domain}/verify")
        d = body["data"]
        return DomainVerification(
            domain=d["domain"],
            dkim_status=d["dkim_status"],
            cname_status=d["cname_status"],
            ownership_verified=d.get("ownership_verified"),
            dns=d.get("dns"),
        )
