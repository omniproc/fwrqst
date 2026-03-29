# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Tufin SecureChange API client and high-level ticket service.

``SecureChangeClient`` is a thin HTTP wrapper around the SecureChange
REST endpoints.  ``AccessRequestService`` provides a higher-level
interface that converts between domain models and Tufin DTOs.
"""

# __IMPORTS______________________________________________________________________________________________________________
import ssl
from pathlib import Path

from httpx import BasicAuth

from fwrqst import SETTINGS
from fwrqst.api.client import ApiClient, Proxy
from fwrqst.models.adapter import AccessRequestTicketAdapter
from fwrqst.models.ticket import AccessRequestTicket
from fwrqst.models.tufin_dto import TicketRootDto
from fwrqst.settings import (
    KEY_SECURE_CHANGE_API_BASE_PATH,
    KEY_SECURE_CHANGE_DOMAIN,
    KEY_SECURE_CHANGE_PORT,
)

# --- Tufin SecureChange API constants -------------------------------------------------
_TICKETS_ENDPOINT = "/tickets"
_TICKET_CANCEL_SUFFIX = "/cancel"
_TICKET_RESPONSE_ID_KEY = "id"

# Standard JSON headers required by the Tufin SecureChange API.
_CONTENT_TYPE_JSON = "application/json"
_REQUEST_TYPE_ACCESS_REQUEST = "ACCESS_REQUEST"


# __PROGRAM______________________________________________________________________________________________________________
def _create_sslctx(cafile: Path | str | None = None) -> ssl.SSLContext:
    """Create a hardened SSL context for Tufin API connections.

    Enables hostname verification, requires peer certificates, and
    enforces TLS 1.2 as the minimum protocol version.  When *cafile*
    is ``None`` the platform's default CA bundle is used.
    """
    sslctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=cafile)
    sslctx.check_hostname = True
    sslctx.verify_mode = ssl.CERT_REQUIRED
    sslctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return sslctx


class SecureChangeClient(ApiClient):
    """Low-level Tufin SecureChange HTTP client.

    Extends ``ApiClient`` with convenience methods for the three
    ticket operations (GET / POST / PUT).  Constructor defaults are
    pulled from application settings when explicit values are not
    supplied.
    """

    def __init__(
        self,
        auth: BasicAuth,
        sslctx: ssl.SSLContext,
        domain: str | None = SETTINGS.get(KEY_SECURE_CHANGE_DOMAIN, None),
        base: str = SETTINGS.get(KEY_SECURE_CHANGE_API_BASE_PATH, None),
        port: int | None = SETTINGS.get(KEY_SECURE_CHANGE_PORT, None),
        proxy: Proxy = ApiClient._PROXY,
        **kwargs,
    ):
        if not domain and not SETTINGS.get(KEY_SECURE_CHANGE_DOMAIN, None):
            raise ValueError("No domain provided.")
        if not port and not SETTINGS.get(KEY_SECURE_CHANGE_PORT, None):
            raise ValueError("No port provided.")
        if not base and not SETTINGS.get(KEY_SECURE_CHANGE_API_BASE_PATH, None):
            raise ValueError("No api base path provided.")

        # Fall back to settings if not provided directly
        resolved_domain = domain or SETTINGS.get(KEY_SECURE_CHANGE_DOMAIN)
        resolved_port: int = port or SETTINGS.get(KEY_SECURE_CHANGE_PORT)
        super().__init__(
            domain=resolved_domain, auth=auth, base=base, port=resolved_port, sslctx=sslctx, proxy=proxy, **kwargs
        )

    def get_ticket(self, path: str, **kwargs):
        """Send a GET request to the given *path* appended to the base URL."""
        data = self.get(f"{self.url}{path}", **kwargs)
        return data

    def put_ticket(self, path: str, **kwargs):
        """Send a PUT request to the given *path* appended to the base URL."""
        return self.put(f"{self.url}{path}", **kwargs)

    def post_ticket(self, path: str, **kwargs):
        """Send a POST request to the given *path* appended to the base URL."""
        return self.post(f"{self.url}{path}", **kwargs)


class AccessRequestService:
    """High-level ticket operations using the SecureChange API.

    Settings are resolved via three mechanisms (highest precedence first):

    1. Direct parameters passed to the constructor.
    2. Environment variables (``FWRQST_SECURE_CHANGE_*``).
    3. Configuration file (``settings.toml``).
    """

    _headers = {
        "Content-Type": _CONTENT_TYPE_JSON,
        "Accept": _CONTENT_TYPE_JSON,
        "type": _REQUEST_TYPE_ACCESS_REQUEST,
    }

    def __init__(
        self,
        username: str,
        password: str,
        domain: str | None = None,
        port: int | None = None,
        cafile: Path | str | None = None,
        **kwargs,
    ):
        sslctx = _create_sslctx(cafile=cafile)

        client = SecureChangeClient(
            auth=BasicAuth(username=username, password=password), domain=domain, port=port, sslctx=sslctx, **kwargs
        )
        client.headers.update(self._headers)
        self.client = client

    def get_ticket(self, ticket_id: str) -> AccessRequestTicket:
        """Retrieve a single ticket by *ticket_id* and return the domain model."""
        data = self.client.get_ticket(f"{_TICKETS_ENDPOINT}/{ticket_id}")
        ticket_dto = TicketRootDto.model_validate(data.json())
        return AccessRequestTicketAdapter.from_dto(data=ticket_dto)

    def create_ticket(self, ticket: AccessRequestTicket) -> str:
        """Submit a new access request ticket.  Returns the server-assigned ticket ID."""
        ticket_dto = AccessRequestTicketAdapter.to_dto(data=ticket)
        response = self.client.post_ticket(_TICKETS_ENDPOINT, data=ticket_dto.model_dump(mode="json", by_alias=True))
        return str(response.json()[_TICKET_RESPONSE_ID_KEY])

    def cancel_ticket(self, ticket_id: str) -> None:
        """Cancel a pending access request by *ticket_id*."""
        self.client.put_ticket(f"{_TICKETS_ENDPOINT}/{ticket_id}{_TICKET_CANCEL_SUFFIX}")
