# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
from conftest import (
    create_access_request_ticket,
    create_dns_endpoint,
    create_ip_endpoint,
    create_ip_range_endpoint,
    create_object_endpoint,
    create_service,
)
from hypothesis import HealthCheck, given, settings

from fwrqst.models.adapter import (
    AccessRequestTicketAdapter,
    EndpointAdapter,
    ServiceAdapter,
)


# __PROGRAM____________________________________________________________________________________________________________
@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(ticket=create_access_request_ticket())
def test_convert_access_request_ticket(ticket):
    """A ticket should survive a full domain → DTO → domain round-trip."""
    subject = ticket.subject

    request_dto = AccessRequestTicketAdapter.to_dto(data=ticket)
    assert request_dto.ticket.subject == subject

    request_mdl = AccessRequestTicketAdapter.from_dto(data=request_dto)
    assert request_mdl.subject == subject


@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(endpoint=create_ip_endpoint())
def test_ip_endpoint_roundtrip(endpoint):
    """An IP endpoint should survive a domain → DTO → domain round-trip."""
    dto = EndpointAdapter.to_dto(endpoint)
    result = EndpointAdapter.from_dto(dto)
    assert result.kind == endpoint.kind
    assert str(result.address) == str(endpoint.address)
    assert result.cidr == endpoint.cidr


@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(endpoint=create_ip_range_endpoint())
def test_ip_range_endpoint_roundtrip(endpoint):
    """An IP range endpoint should survive a domain → DTO → domain round-trip."""
    dto = EndpointAdapter.to_dto(endpoint)
    result = EndpointAdapter.from_dto(dto)
    assert result.kind == endpoint.kind
    assert str(result.start) == str(endpoint.start)
    assert str(result.end) == str(endpoint.end)


@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(endpoint=create_dns_endpoint())
def test_dns_endpoint_roundtrip(endpoint):
    """A DNS endpoint should survive a domain → DTO → domain round-trip."""
    dto = EndpointAdapter.to_dto(endpoint)
    result = EndpointAdapter.from_dto(dto)
    assert result.kind == endpoint.kind
    assert result.fqdn == endpoint.fqdn


@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(endpoint=create_object_endpoint())
def test_object_endpoint_roundtrip(endpoint):
    """A Tufin object endpoint should survive a domain → DTO → domain round-trip."""
    dto = EndpointAdapter.to_dto(endpoint)
    result = EndpointAdapter.from_dto(dto)
    assert result.kind == endpoint.kind
    assert result.name == endpoint.name
    assert result.manager == endpoint.manager


@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(service=create_service())
def test_service_roundtrip(service):
    """A TCP/UDP service should survive a domain → DTO → domain round-trip."""
    dto = ServiceAdapter.to_dto(service)
    result = ServiceAdapter.from_dto(dto)
    assert result.protocol == service.protocol
    assert result.port == service.port
