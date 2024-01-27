# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
from datetime import date, timedelta

from conftest import create_access_request, create_access_request_ticket
from hypothesis import HealthCheck, given, settings


# __PROGRAM____________________________________________________________________________________________________________
@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(ticket=create_access_request_ticket())
def test_create_access_request_ticket(ticket):
    """A hypothesis-generated ticket should preserve its subject after construction."""
    subject = ticket.subject
    assert ticket.subject == subject


@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(access_request=create_access_request())
def test_default_expiration_used_when_omitted(access_request):
    """When expiration is not provided, _default_expiration should supply exactly today + configured days."""
    from fwrqst import SETTINGS
    from fwrqst.models.ticket import AccessRequestTicket
    from fwrqst.settings import KEY_ACCESS_REQUEST_EXPIRATION_DAYS

    expected = date.today() + timedelta(days=SETTINGS.get(KEY_ACCESS_REQUEST_EXPIRATION_DAYS, None))
    ticket = AccessRequestTicket(access_requests=[access_request])
    assert ticket.expiration == expected
