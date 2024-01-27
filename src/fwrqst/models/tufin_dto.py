# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Data-transfer objects (DTOs) that mirror the Tufin SecureChange JSON API.

These Pydantic models are a 1 1 mapping of the request/response bodies used
by the Tufin REST API.  Field aliases (``@type``, ``@xsi.type``,
``expiration_date``, …) match the exact keys the API expects so that
``model_dump(by_alias=True)`` produces spec-compliant payloads.
"""

# __IMPORTS______________________________________________________________________________________________________________
import ipaddress
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, SerializeAsAny, model_validator

from fwrqst.models.types import (
    Action,
    EndpointType,
    Priority,
    ProtocolType,
    RequestType,
    ServiceType,
)


# __MODEL________________________________________________________________________________________________________________
class WorkflowDto(BaseModel, populate_by_name=True, use_enum_values=True):
    name: str


class ServiceDto(BaseModel, populate_by_name=True, use_enum_values=True):
    kind: Annotated[str, Field(alias="@type")]


class ProtocolServiceDto(ServiceDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[ServiceType.PROTOCOL], Field(alias="@type")] = ServiceType.PROTOCOL.value
    protocol: Annotated[str, Field()]


class PredefinedServiceDto(ServiceDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[ServiceType.PREDEFINED], Field(alias="@type")] = ServiceType.PREDEFINED.value


class TCPProtocolServiceDto(ProtocolServiceDto, populate_by_name=True, use_enum_values=True):
    port: int
    protocol: Annotated[Literal[ProtocolType.TCP], Field()] = ProtocolType.TCP.value


class UDPProtocolServiceDto(ProtocolServiceDto, populate_by_name=True, use_enum_values=True):
    port: int
    protocol: Annotated[Literal[ProtocolType.UDP], Field()] = ProtocolType.UDP.value


class ServicesDto(BaseModel, populate_by_name=True, use_enum_values=True):
    service: list[Annotated[TCPProtocolServiceDto | UDPProtocolServiceDto, Field(discriminator="protocol")]]


class EndpointDto(BaseModel, populate_by_name=True, use_enum_values=True):
    kind: Annotated[SerializeAsAny[EndpointType], Field(alias="@type")]


class IpEndpointDto(EndpointDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[EndpointType.IP], Field(alias="@type")] = EndpointType.IP.value
    address: Annotated[str, Field(alias="ip_address")]
    cidr: Annotated[int, Field(default=32)]


class IpRangeEndpointDto(EndpointDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[EndpointType.RANGE], Field(alias="@type")] = EndpointType.RANGE.value
    start: Annotated[str, Field(alias="range_first_ip")]
    end: Annotated[str, Field(alias="range_last_ip")]

    @model_validator(mode="after")
    def validate_range(self) -> "IpRangeEndpointDto":
        """Validate range of IP addresses."""

        first_ip = self.start
        last_ip = self.end

        if ipaddress.ip_address(first_ip) >= ipaddress.ip_address(last_ip):
            raise ValueError(f"First IP '{first_ip}' >= last IP '{last_ip}'")  # pragma: no cover

        return self


class DnsEndpointDto(EndpointDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[EndpointType.DNS], Field(alias="@type")] = EndpointType.DNS.value
    fqdn: Annotated[str, Field(alias="host_name")]


class ObjectEndpointDto(EndpointDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[EndpointType.OBJECT], Field(alias="@type")] = EndpointType.OBJECT.value
    name: Annotated[str, Field(alias="object_name")]
    manager: Annotated[str, Field(alias="management_name")]


class SourcesDto(BaseModel, populate_by_name=True, use_enum_values=True):
    source: list[
        Annotated[IpEndpointDto | IpRangeEndpointDto | DnsEndpointDto | ObjectEndpointDto, Field(discriminator="kind")]
    ]


class DestinationsDto(BaseModel, populate_by_name=True, use_enum_values=True):
    destination: list[
        Annotated[IpEndpointDto | IpRangeEndpointDto | DnsEndpointDto | ObjectEndpointDto, Field(discriminator="kind")]
    ]


class AccessRequestDto(BaseModel, populate_by_name=True, use_enum_values=True):
    sources: Annotated[SourcesDto, Field()]
    destinations: Annotated[DestinationsDto, Field()]
    services: Annotated[ServicesDto, Field()]
    source_domain: Annotated[str, Field()]
    destination_domain: Annotated[str, Field()]
    action: Annotated[SerializeAsAny[Action], Field()]
    comment: Annotated[str, Field()] = ""


class FieldDto(BaseModel, populate_by_name=True, use_enum_values=True):
    kind: Annotated[RequestType, Field(alias="@xsi.type")]


class AccessRequestFieldDto(FieldDto, populate_by_name=True, use_enum_values=True):
    kind: Annotated[Literal[RequestType.MULTI_ACCESS_REQUEST], Field(alias="@xsi.type")] = (
        RequestType.MULTI_ACCESS_REQUEST.value
    )

    access_request: Annotated[list[AccessRequestDto], Field()]


class FieldsDto(BaseModel, populate_by_name=True, use_enum_values=True):
    field: list[Annotated[AccessRequestFieldDto, Field(discriminator="kind")]]


class TaskDto(BaseModel, populate_by_name=True, use_enum_values=True):
    fields: SerializeAsAny[FieldsDto]


class TasksDto(BaseModel, populate_by_name=True, use_enum_values=True):
    task: list[SerializeAsAny[TaskDto]] | SerializeAsAny[TaskDto]


class StepDto(BaseModel, populate_by_name=True, use_enum_values=True):
    tasks: SerializeAsAny[TasksDto]


class StepsDto(BaseModel, populate_by_name=True, use_enum_values=True):
    step: list[SerializeAsAny[StepDto]]


class TicketDto(BaseModel, populate_by_name=True, use_enum_values=True):
    subject: Annotated[str, Field()]
    priority: Annotated[Priority, Field()]
    expiration: Annotated[date, Field(alias="expiration_date")]
    workflow: SerializeAsAny[WorkflowDto]
    steps: Annotated[SerializeAsAny[StepsDto], Field(default=StepsDto(step=[]))]


class TicketRootDto(BaseModel, populate_by_name=True, use_enum_values=True):
    ticket: SerializeAsAny[TicketDto]


class TicketsRootDto(BaseModel, populate_by_name=True, use_enum_values=True):
    tickets: list[SerializeAsAny[TicketDto]]


class AccessRequestTicketDto(TicketDto, populate_by_name=True, use_enum_values=True):
    steps: Annotated[SerializeAsAny[StepsDto], Field()]
