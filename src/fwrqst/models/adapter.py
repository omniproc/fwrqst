# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Bidirectional adapters between domain models and Tufin DTOs.

Each adapter converts between the user-facing ticket/endpoint/service
models (``fwrqst.models.ticket``) and the API-facing DTO objects
(``fwrqst.models.tufin_dto``).  The conversion is used when reading
tickets from the Tufin API and when posting new tickets.
"""

# __IMPORTS______________________________________________________________________________________________________________
import ipaddress

from fwrqst.models.ticket import (
    AccessRequest,
    AccessRequestTicket,
    DnsEndpoint,
    IpEndpoint,
    IPRangeEndpoint,
    ObjectEndpoint,
    TcpService,
    UdpService,
)
from fwrqst.models.tufin_dto import (
    AccessRequestDto,
    AccessRequestFieldDto,
    AccessRequestTicketDto,
    DestinationsDto,
    DnsEndpointDto,
    EndpointDto,
    FieldsDto,
    IpEndpointDto,
    IpRangeEndpointDto,
    ObjectEndpointDto,
    ServicesDto,
    SourcesDto,
    StepDto,
    StepsDto,
    TaskDto,
    TasksDto,
    TCPProtocolServiceDto,
    TicketRootDto,
    UDPProtocolServiceDto,
    WorkflowDto,
)


# __PROGRAM______________________________________________________________________________________________________________
class EndpointAdapter:
    """Convert between domain Endpoint models and Tufin EndpointDto objects."""

    @classmethod
    def from_dto(cls, data: EndpointDto) -> IpEndpoint | IPRangeEndpoint | DnsEndpoint | ObjectEndpoint:
        """Map a Tufin endpoint DTO to the corresponding domain model."""
        match data:
            case IpEndpointDto(address=address, cidr=cidr):
                return IpEndpoint(address=ipaddress.ip_address(address), cidr=cidr)
            case IpRangeEndpointDto(start=start, end=end):
                return IPRangeEndpoint(start=ipaddress.ip_address(start), end=ipaddress.ip_address(end))
            case DnsEndpointDto(fqdn=fqdn):
                return DnsEndpoint(fqdn=fqdn)
            case ObjectEndpointDto(name=name, manager=manager):
                return ObjectEndpoint(name=name, manager=manager)
            case _:  # pragma: no cover
                raise ValueError(f"Invalid endpoint type: {data}")

    @classmethod
    def to_dto(
        cls, data: IpEndpoint | IPRangeEndpoint | DnsEndpoint | ObjectEndpoint
    ) -> IpEndpointDto | IpRangeEndpointDto | DnsEndpointDto | ObjectEndpointDto:
        """Map a domain endpoint model to the corresponding Tufin DTO."""
        if isinstance(data, IpEndpoint):
            return IpEndpointDto(address=str(data.address), cidr=data.cidr)
        elif isinstance(data, IPRangeEndpoint):
            return IpRangeEndpointDto(start=str(data.start), end=str(data.end))
        elif isinstance(data, DnsEndpoint):
            return DnsEndpointDto(fqdn=data.fqdn)
        elif isinstance(data, ObjectEndpoint):
            return ObjectEndpointDto(name=data.name, manager=data.manager)
        raise ValueError(f"Invalid endpoint kind: {data.kind}")  # pragma: no cover


class ServiceAdapter:
    """Convert between domain Service models and Tufin ServiceDto objects."""

    @classmethod
    def from_dto(cls, data: TCPProtocolServiceDto | UDPProtocolServiceDto) -> TcpService | UdpService:
        """Map a Tufin service DTO to the corresponding domain model."""
        if isinstance(data, TCPProtocolServiceDto):
            return TcpService(port=data.port)
        elif isinstance(data, UDPProtocolServiceDto):
            return UdpService(port=data.port)
        raise ValueError(f"Invalid service type: {data.kind}")  # pragma: no cover

    @classmethod
    def to_dto(cls, data: TcpService | UdpService) -> TCPProtocolServiceDto | UDPProtocolServiceDto:
        """Map a domain service model to the corresponding Tufin DTO."""
        if isinstance(data, TcpService):
            return TCPProtocolServiceDto(port=data.port)
        elif isinstance(data, UdpService):
            return UDPProtocolServiceDto(port=data.port)
        raise ValueError(f"Invalid service protocol: {data.protocol}")  # pragma: no cover


class AccessRequestTicketAdapter:
    """Convert between domain AccessRequestTicket and the Tufin TicketRootDto."""

    @classmethod
    def from_dto(cls, data: TicketRootDto) -> AccessRequestTicket:
        """Deserialise a full Tufin ticket response into a domain ticket model."""
        ticket = data.ticket

        try:
            task = ticket.steps.step[0].tasks.task
            if isinstance(task, list):
                task = task[0]
            access_requests_dto = task.fields.field[0].access_request
        except AttributeError, IndexError:  # pragma: no cover
            access_requests_dto = []

        access_requests = []
        for ar in access_requests_dto:
            access_requests.append(
                AccessRequest(
                    comment=getattr(ar, "comment", ""),
                    action=ar.action,
                    source_domain=ar.source_domain,
                    destination_domain=ar.destination_domain,
                    sources=[EndpointAdapter.from_dto(s) for s in ar.sources.source],
                    destinations=[EndpointAdapter.from_dto(d) for d in ar.destinations.destination],
                    services=[ServiceAdapter.from_dto(s) for s in ar.services.service],
                )
            )

        return AccessRequestTicket(
            subject=ticket.subject,
            priority=ticket.priority,
            expiration=ticket.expiration,
            workflow=ticket.workflow.name,
            access_requests=access_requests,
        )

    @classmethod
    def to_dto(cls, data: AccessRequestTicket) -> TicketRootDto:
        """Serialise a domain ticket model into the Tufin DTO structure."""
        access_requests = []
        for request in data.access_requests:
            access_requests.append(
                AccessRequestDto(
                    source_domain=request.source_domain,
                    sources=SourcesDto(source=[EndpointAdapter.to_dto(source) for source in request.sources]),
                    destination_domain=request.destination_domain,
                    destinations=DestinationsDto(
                        destination=[EndpointAdapter.to_dto(destination) for destination in request.destinations]
                    ),
                    services=ServicesDto(service=[ServiceAdapter.to_dto(service) for service in request.services]),
                    action=request.action,
                    comment=request.comment,
                )
            )

        return TicketRootDto(
            ticket=AccessRequestTicketDto(
                subject=data.subject,
                priority=data.priority,
                expiration=data.expiration,
                workflow=WorkflowDto(name=data.workflow),
                steps=StepsDto(
                    step=[
                        StepDto(
                            tasks=TasksDto(
                                task=TaskDto(fields=FieldsDto(field=[AccessRequestFieldDto(access_request=access_requests)]))
                            )
                        )
                    ]
                ),
            )
        )
