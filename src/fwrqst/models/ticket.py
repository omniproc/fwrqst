# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Pydantic models for access request tickets.

These are the canonical domain models used throughout the application.
Each model maps 1 1 to the fields in the user-facing YAML schema and is
converted to/from Tufin DTO objects via the adapter layer.
"""

# __IMPORTS______________________________________________________________________________________________________________
from datetime import date, timedelta
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated, Literal

from pydantic import BaseModel, Field, RootModel, model_validator

from fwrqst import SETTINGS
from fwrqst.models.types import Action, EndpointType, Priority, ProtocolType
from fwrqst.settings import (
    KEY_ACCESS_REQUEST_DOMAIN,
    KEY_ACCESS_REQUEST_EXPIRATION_DAYS,
    KEY_ACCESS_REQUEST_PRIORITY,
    KEY_ACCESS_REQUEST_SUBJECT,
    KEY_ACCESS_REQUEST_WORKFLOW,
)


# __MODEL________________________________________________________________________________________________________________
def _strip_default_from_schema(s):
    """Remove the 'default' key from a JSON schema node so it doesn't leak into the public schema."""
    s.pop("default")


def _add_kind_to_required(s):
    """Append 'kind' to the required field list of a JSON schema node."""
    s["required"].append("kind")


def _add_protocol_to_required(s):
    """Append 'protocol' to the required field list of a JSON schema node."""
    s["required"].append("protocol")


class Service(BaseModel, title="A network service", use_enum_values=True):
    """
    A network service
    """

    protocol: ProtocolType = Field(description="The protocol of this service")


class TcpService(Service, title="TCP network service", use_enum_values=True, json_schema_extra=_add_protocol_to_required):
    """
    TCP network service
    """

    protocol: Annotated[
        Literal[ProtocolType.TCP], Field(description="TCP protocol type", json_schema_extra=_strip_default_from_schema)
    ] = ProtocolType.TCP
    port: int = Field(description="The port of this service", ge=0, le=65535)


class UdpService(Service, title="UDP network service", use_enum_values=True, json_schema_extra=_add_protocol_to_required):
    """
    UDP network service
    """

    protocol: Annotated[
        Literal[ProtocolType.UDP], Field(description="UDP protocol type", json_schema_extra=_strip_default_from_schema)
    ] = ProtocolType.UDP
    port: int = Field(description="The port of this service", ge=0, le=65535)


class Endpoint(BaseModel, title="A network endpoint", use_enum_values=True):
    """
    A network endpoint
    """

    kind: EndpointType = Field(description="The endpoint kind")


class IpEndpoint(Endpoint, title="IP Address", use_enum_values=True, json_schema_extra=_add_kind_to_required):
    """
    An IP address network endpoint
    """

    kind: Annotated[
        Literal[EndpointType.IP], Field(description="IP address endpoint", json_schema_extra=_strip_default_from_schema)
    ] = EndpointType.IP
    address: IPv4Address | IPv6Address = Field(description="The IP address of this endpoint")
    cidr: int = Field(description="The CIDR of this endpoint", ge=0, le=128)


class IPRangeEndpoint(Endpoint, title="IP Range", use_enum_values=True, json_schema_extra=_add_kind_to_required):
    """
    An IP network range endpoint
    """

    kind: Annotated[
        Literal[EndpointType.RANGE], Field(description="IP range endpoint", json_schema_extra=_strip_default_from_schema)
    ] = EndpointType.RANGE
    start: IPv4Address | IPv6Address = Field(description="The start IP address of this endpoint")
    end: IPv4Address | IPv6Address = Field(description="The end IP address of this endpoint")


class DnsEndpoint(Endpoint, title="DNS Name", use_enum_values=True, json_schema_extra=_add_kind_to_required):
    """
    A DNS network endpoint
    """

    kind: Annotated[
        Literal[EndpointType.DNS], Field(description="DNS endpoint", json_schema_extra=_strip_default_from_schema)
    ] = EndpointType.DNS
    fqdn: str = Field(description="Valid DNS Fully Qualified Domain Name as specified by RFC5890 section 2.3.2.3")


class ObjectEndpoint(Endpoint, title="Tufin Object", use_enum_values=True, json_schema_extra=_add_kind_to_required):
    """
    A pre-defined Tufin object endpoint
    """

    kind: Annotated[
        Literal[EndpointType.OBJECT], Field(description="Object endpoint", json_schema_extra=_strip_default_from_schema)
    ] = EndpointType.OBJECT
    name: str = Field(description="The name of the Tufin object")
    manager: str = Field(description="The Tufin management name in charge of the Tufin object")


class AccessRequest(BaseModel, title="Access Request", use_enum_values=True):
    """
    A Tufin access request
    """

    comment: str = Field(description="A meaningful comment for this access request", default="")
    action: Action = Field(
        description="The action to perform when a connection matches the defined rule", default=Action.ACCEPT
    )
    source_domain: str = Field(
        description="The Tufin domain of the source endpoint",
        min_length=1,
        validate_default=True,
        default=SETTINGS.get(KEY_ACCESS_REQUEST_DOMAIN, None),
    )
    sources: Annotated[
        list[
            Annotated[
                IpEndpoint | IPRangeEndpoint | DnsEndpoint | ObjectEndpoint,
                Field(discriminator="kind"),
            ]
        ],
        Field(description="list of source endpoints to allow", min_length=1),
    ]
    destination_domain: str = Field(
        description="The Tufin domain of the destination endpoint",
        min_length=1,
        validate_default=True,
        default=SETTINGS.get(KEY_ACCESS_REQUEST_DOMAIN, None),
    )
    destinations: Annotated[
        list[
            Annotated[
                IpEndpoint | IPRangeEndpoint | DnsEndpoint | ObjectEndpoint,
                Field(discriminator="kind"),
            ]
        ],
        Field(description="list of destination endpoints to allow", min_length=1),
    ]
    services: Annotated[
        list[Annotated[TcpService | UdpService, Field(discriminator="protocol")]],
        Field(description="list of services to allow", min_length=1),
    ]


def _default_expiration() -> date:
    """Calculate the default expiration date from today using the configured number of days."""
    return date.today() + timedelta(days=SETTINGS.get(KEY_ACCESS_REQUEST_EXPIRATION_DAYS, None))


class AccessRequestTicket(BaseModel, title="Access Request Ticket", use_enum_values=True):
    """
    A Tufin access request ticket, wrapping one or more Tufin access request
    """

    subject: Annotated[
        str,
        Field(description="Subject of this Tufin access request ticket", min_length=1, validate_default=True),
    ] = SETTINGS.get(KEY_ACCESS_REQUEST_SUBJECT, None)

    workflow: Annotated[
        str,
        Field(
            description="Name of the Tufin workflow to use",
            min_length=1,
            validate_default=True,
        ),
    ] = SETTINGS.get(KEY_ACCESS_REQUEST_WORKFLOW, None)

    priority: Annotated[
        Priority,
        Field(
            description="Priority of this Tufin access request ticket",
            validate_default=True,
        ),
    ] = SETTINGS.get(KEY_ACCESS_REQUEST_PRIORITY, None)

    expiration: Annotated[
        date,
        Field(
            description="Date when the changes requested in this ticket expire in ISO 8601 format",
            default_factory=_default_expiration,
            validate_default=True,
        ),
    ]

    access_requests: Annotated[list[AccessRequest], Field(description="list of access requests", min_length=1)]

    @model_validator(mode="after")
    def validate_expiration(self) -> "AccessRequestTicket":
        _min_expiration = date.today()
        _max_expiration = _min_expiration + timedelta(days=SETTINGS.get("ACCESS_REQUEST_MAX_EXPIRATION_DAYS", None))

        if not self.expiration:  # pragma: no cover
            self._expiration = _max_expiration
            return self
        if self.expiration > _max_expiration:
            raise ValueError(f"Maximum allowed expiration date is {_max_expiration.isoformat()}")  # pragma: no cover
        if self.expiration < _min_expiration:
            raise ValueError(f"Minimum allowed expiration date is {_min_expiration.isoformat()}")  # pragma: no cover

        return self


class AccessRequestTickets(RootModel, title="Access Request Tickets", use_enum_values=True):
    """
    A collection of Tufin access request tickets
    """

    root: list[AccessRequestTicket]

    def __iter__(self):
        return iter(self.root)  # pragma: no cover

    def __getitem__(self, item):
        return self.root[item]  # pragma: no cover
