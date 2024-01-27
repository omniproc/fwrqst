# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
import pytest
from conftest import create_access_request_ticket
from hypothesis import HealthCheck, given, settings

from fwrqst.api.securechange import AccessRequestService
from fwrqst.models.adapter import AccessRequestTicketAdapter
from fwrqst.models.ticket import AccessRequestTicket


# __PROGRAM____________________________________________________________________________________________________________
def test_get_ticket(
    httpx_mock,
    fix_tufin_domain,
    fix_tufin_username,
    fix_tufin_password,
    fix_access_request_ticket_dto,
    fix_access_request_ticket,
):
    svc = AccessRequestService(domain=fix_tufin_domain, username=fix_tufin_username, password=fix_tufin_password)
    httpx_mock.add_response(
        url=f"{svc.client.url}/tickets/999999", json=fix_access_request_ticket_dto, status_code=200, method="GET"
    )

    response = svc.get_ticket(ticket_id="999999")
    assert response.model_dump(mode="json", by_alias=True) == fix_access_request_ticket


def test_create_ticket(httpx_mock, fix_tufin_domain, fix_tufin_username, fix_tufin_password, fix_access_request_ticket):
    svc = AccessRequestService(domain=fix_tufin_domain, username=fix_tufin_username, password=fix_tufin_password)
    httpx_mock.add_response(url=f"{svc.client.url}/tickets", json={"id": "999999"}, status_code=201, method="POST")

    ticket = AccessRequestTicket.model_validate(fix_access_request_ticket)
    response = svc.create_ticket(ticket=ticket)
    assert response == "999999"


def test_cancel_ticket(httpx_mock, fix_tufin_domain, fix_tufin_username, fix_tufin_password):
    svc = AccessRequestService(domain=fix_tufin_domain, username=fix_tufin_username, password=fix_tufin_password)
    httpx_mock.add_response(url=f"{svc.client.url}/tickets/999999/cancel", status_code=200, method="PUT")

    svc.cancel_ticket(ticket_id="999999")


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(ticket=create_access_request_ticket())
def test_get_ticket_roundtrip(
    ticket,
    httpx_mock,
    fix_tufin_domain,
    fix_tufin_username,
    fix_tufin_password,
):
    """Property-based test: any valid ticket should survive a GET round-trip through the API layer."""
    ticket_dto = AccessRequestTicketAdapter.to_dto(data=ticket)
    dto_json = ticket_dto.model_dump(mode="json", by_alias=True)

    svc = AccessRequestService(domain=fix_tufin_domain, username=fix_tufin_username, password=fix_tufin_password)
    httpx_mock.add_response(
        url=f"{svc.client.url}/tickets/1",
        json=dto_json,
        status_code=200,
        method="GET",
    )

    result = svc.get_ticket(ticket_id="1")
    assert result.model_dump(mode="json") == ticket.model_dump(mode="json")


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
@given(ticket=create_access_request_ticket())
def test_create_ticket_roundtrip(
    ticket,
    httpx_mock,
    fix_tufin_domain,
    fix_tufin_username,
    fix_tufin_password,
):
    """Property-based test: any valid ticket should be creatable through the API layer."""
    svc = AccessRequestService(domain=fix_tufin_domain, username=fix_tufin_username, password=fix_tufin_password)
    httpx_mock.add_response(
        url=f"{svc.client.url}/tickets",
        json={"id": "12345"},
        status_code=201,
        method="POST",
    )

    result = svc.create_ticket(ticket=ticket)
    assert result == "12345"
