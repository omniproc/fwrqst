# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
from datetime import date, timedelta

import pytest
from hypothesis import assume
from hypothesis import provisional as pv
from hypothesis import strategies as st
from hypothesis.strategies import composite

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
from fwrqst.models.types import Action, Priority

# __GLOBALS____________________________________________________________________________________________________________
today = date.today()
min_date = today + timedelta(days=1)
max_date = today + timedelta(days=364)


# __PROGRAM____________________________________________________________________________________________________________
@composite
def create_ipv4_endpoint(draw) -> IpEndpoint:
    """Generate a random IPv4 endpoint with a valid CIDR mask."""
    return IpEndpoint(address=draw(st.ip_addresses(v=4)), cidr=draw(st.integers(min_value=0, max_value=32)))


@composite
def create_ipv6_endpoint(draw) -> IpEndpoint:
    """Generate a random IPv6 endpoint with a valid CIDR mask."""
    return IpEndpoint(address=draw(st.ip_addresses(v=6)), cidr=draw(st.integers(min_value=0, max_value=128)))


@composite
def create_ip_endpoint(draw) -> IpEndpoint:
    """Generate either an IPv4 or IPv6 endpoint."""
    return draw(st.one_of(create_ipv4_endpoint(), create_ipv6_endpoint()))


@composite
def create_ipv4_range_endpoint(draw) -> IPRangeEndpoint:
    """Generate a random IPv4 range where start < end."""
    start = draw(st.ip_addresses(v=4))
    end = draw(st.ip_addresses(v=4))

    ip_range = IPRangeEndpoint(start=start, end=end)
    assume(start < end)
    return ip_range


@composite
def create_ipv6_range_endpoint(draw) -> IPRangeEndpoint:
    """Generate a random IPv6 range where start < end."""
    start = draw(st.ip_addresses(v=6))
    end = draw(st.ip_addresses(v=6))

    ip_range = IPRangeEndpoint(start=start, end=end)
    assume(start < end)
    return ip_range


@composite
def create_ip_range_endpoint(draw) -> IPRangeEndpoint:
    """Generate either an IPv4 or IPv6 range endpoint."""
    return draw(st.one_of(create_ipv4_range_endpoint(), create_ipv6_range_endpoint()))


@composite
def create_dns_endpoint(draw) -> DnsEndpoint:
    """Generate a random DNS endpoint from a valid domain name."""
    return DnsEndpoint(fqdn=draw(pv.domains(max_length=255, max_element_length=63)))


@composite
def create_object_endpoint(draw) -> ObjectEndpoint:
    """Generate a random Tufin object endpoint with arbitrary name and manager."""
    return ObjectEndpoint(
        name=draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=1, max_size=30)),
        manager=draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=1, max_size=30)),
    )


@composite
def create_endpoint(draw) -> IpEndpoint | IPRangeEndpoint | DnsEndpoint | ObjectEndpoint:
    """Generate a random endpoint of any supported type."""
    endpoint_cls = draw(st.sampled_from([IpEndpoint, IPRangeEndpoint, DnsEndpoint, ObjectEndpoint]))
    if endpoint_cls == IpEndpoint:
        return draw(create_ip_endpoint())
    elif endpoint_cls == IPRangeEndpoint:
        return draw(create_ip_range_endpoint())
    elif endpoint_cls == DnsEndpoint:
        return draw(create_dns_endpoint())
    elif endpoint_cls == ObjectEndpoint:
        return draw(create_object_endpoint())
    else:
        raise ValueError("Invalid endpoint type")


@composite
def create_service(draw) -> TcpService | UdpService:
    """Generate a random TCP or UDP service on a valid port."""
    service_cls = draw(st.sampled_from([TcpService, UdpService]))
    if service_cls == TcpService:
        return draw(st.builds(TcpService, port=st.integers(min_value=1, max_value=65535)))
    else:
        return draw(st.builds(UdpService, port=st.integers(min_value=1, max_value=65535)))


@composite
def create_access_request(draw) -> AccessRequest:
    """Generate a random access request with valid endpoints, services, and domains."""
    comment = draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=0, max_size=30))
    action = draw(st.sampled_from(Action))
    source_domain = draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=1, max_size=30))
    destination_domain = draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=1, max_size=30))
    sources = draw(st.lists(create_endpoint(), min_size=1, max_size=10))
    destinations = draw(st.lists(create_endpoint(), min_size=1, max_size=10))
    services = draw(st.lists(create_service(), min_size=1, max_size=10))

    return AccessRequest(
        comment=comment,
        action=action,
        source_domain=source_domain,
        destination_domain=destination_domain,
        sources=sources,
        destinations=destinations,
        services=services,
    )


@composite
def create_access_request_ticket(draw) -> AccessRequestTicket:
    """Generate a random access request ticket with valid fields and 1–3 access requests."""
    subject = draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=1, max_size=30))
    priority = draw(st.sampled_from(Priority))
    expiration = draw(st.dates(min_value=min_date, max_value=max_date))
    workflow = draw(st.text(alphabet=st.characters(codec="utf-8"), min_size=1, max_size=30))
    access_requests = draw(st.lists(create_access_request(), min_size=1, max_size=3))

    return AccessRequestTicket(
        subject=subject,
        priority=priority,
        workflow=workflow,
        expiration=expiration,
        access_requests=access_requests,
    )


@pytest.fixture(scope="session")
def ticket_mdl_json_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "ticket.mdl.json"


@pytest.fixture(scope="session")
def ticket_mdl_yaml_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "ticket.mdl.yaml"


@pytest.fixture(scope="session")
def ticket_schema_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "ticket.schema.json"


@pytest.fixture(scope="session")
def ticket_dto_json_file(tmp_path_factory):
    return tmp_path_factory.mktemp("data") / "ticket.dto.json"


@pytest.fixture
def fix_tufin_domain():
    return "localhost"


@pytest.fixture
def fix_tufin_username():
    return "dummy"


@pytest.fixture
def fix_tufin_password():
    return "password"


@pytest.fixture(scope="module")
def fix_access_request_ticket():
    _expiration = (date.today() + timedelta(days=30)).isoformat()
    return {
        "subject": "API Test",
        "workflow": "Standard",
        "priority": "Normal",
        "expiration": _expiration,
        "access_requests": [
            {
                "comment": "Rule #1",
                "action": "accept",
                "source_domain": "Default",
                "sources": [{"kind": "IP", "address": "127.0.0.1", "cidr": 32}],
                "destination_domain": "Default",
                "destinations": [{"kind": "DNS", "fqdn": "example.com"}],
                "services": [{"protocol": "TCP", "port": 80}],
            }
        ],
    }


@pytest.fixture(scope="module")
def fix_access_request_ticket_dto():
    _expiration = (date.today() + timedelta(days=30)).isoformat()
    return {
        "ticket": {
            "subject": "API Test",
            "priority": "Normal",
            "expiration_date": _expiration,
            "workflow": {"name": "Standard"},
            "steps": {
                "step": [
                    {
                        "tasks": {
                            "task": {
                                "fields": {
                                    "field": [
                                        {
                                            "@xsi.type": "multi_access_request",
                                            "access_request": [
                                                {
                                                    "sources": {
                                                        "source": [{"@type": "IP", "ip_address": "127.0.0.1", "cidr": 32}]
                                                    },
                                                    "destinations": {
                                                        "destination": [{"@type": "DNS", "host_name": "example.com"}]
                                                    },
                                                    "services": {
                                                        "service": [{"@type": "PROTOCOL", "protocol": "TCP", "port": 80}]
                                                    },
                                                    "source_domain": "Default",
                                                    "destination_domain": "Default",
                                                    "action": "accept",
                                                    "comment": "Rule #1",
                                                }
                                            ],
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            },
        }
    }
