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
from fwrqst.models.ticket import (
    AccessRequest,
    AccessRequestTicket,
    DnsEndpoint,
    Endpoint,
    IpEndpoint,
    IPRangeEndpoint,
    ObjectEndpoint,
    Service,
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
    ServiceDto,
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
from fwrqst.models.types import EndpointType, ProtocolType, ServiceType


# __PROGRAM______________________________________________________________________________________________________________
class EndpointAdapter:
    """Convert between domain Endpoint models and Tufin EndpointDto objects."""

    @classmethod
    def from_dto(cls, data: EndpointDto) -> Endpoint:
        """Map a Tufin endpoint DTO to the corresponding domain model."""
        match data:
            case IpEndpointDto(address=address, cidr=cidr):
                return IpEndpoint(address=address, cidr=cidr)
            case IpRangeEndpointDto(start=start, end=end):
                return IPRangeEndpoint(start=start, end=end)
            case DnsEndpointDto(fqdn=fqdn):
                return DnsEndpoint(fqdn=fqdn)
            case ObjectEndpointDto(name=name, manager=manager):
                return ObjectEndpoint(name=name, manager=manager)
            case _:  # pragma: no cover
                raise ValueError(f"Invalid endpoint type: {data}")

    @classmethod
    def to_dto(cls, data: Endpoint) -> EndpointDto:
        """Map a domain endpoint model to the corresponding Tufin DTO."""
        endpoint = None
        if data.kind == EndpointType.IP:
            endpoint = IpEndpointDto(address=str(data.address), cidr=str(data.cidr))
        elif data.kind == EndpointType.RANGE:
            endpoint = IpRangeEndpointDto(start=str(data.start), end=str(data.end))
        elif data.kind == EndpointType.DNS:
            endpoint = DnsEndpointDto(fqdn=data.fqdn)
        elif data.kind == EndpointType.OBJECT:
            endpoint = ObjectEndpointDto(name=data.name, manager=data.manager)
        else:  # pragma: no cover
            raise ValueError(f"Invalid endpoint kind: {data.kind}")

        return endpoint


class ServiceAdapter:
    """Convert between domain Service models and Tufin ServiceDto objects."""

    @classmethod
    def from_dto(cls, data: ServiceDto) -> Service:
        """Map a Tufin service DTO to the corresponding domain model."""
        match data.kind:
            case ServiceType.PROTOCOL:
                match data.protocol:
                    case ProtocolType.TCP:
                        return TcpService(port=data.port)
                    case ProtocolType.UDP:
                        return UdpService(port=data.port)
                    case _:  # pragma: no cover
                        raise ValueError(f"Invalid protocol type: {data.protocol}")
            case ServiceType.PREDEFINED:  # pragma: no cover
                raise NotImplementedError()
            case _:  # pragma: no cover
                raise ValueError(f"Invalid service type: {data.kind}")

    @classmethod
    def to_dto(cls, data: Service) -> ServiceDto:
        """Map a domain service model to the corresponding Tufin DTO."""
        service = None
        if data.protocol == ProtocolType.TCP:
            service = TCPProtocolServiceDto(port=data.port)
        elif data.protocol == ProtocolType.UDP:
            service = UDPProtocolServiceDto(port=data.port)
        else:  # pragma: no cover
            raise ValueError(f"Invalid service kind: {data.kind}")
        return service


class AccessRequestTicketAdapter:
    """Convert between domain AccessRequestTicket and the Tufin TicketRootDto."""

    @classmethod
    def from_dto(cls, data: TicketRootDto) -> AccessRequestTicket:
        """Deserialise a full Tufin ticket response into a domain ticket model."""
        ticket = data.ticket

        try:
            access_requests_dto = ticket.steps.step[0].tasks.task.fields.field[0].access_request
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
