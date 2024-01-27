# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
import json

import pytest
from conftest import create_access_request_ticket
from hypothesis import HealthCheck, given, settings

from fwrqst.io import dump_tickets, export_schema, load_tickets


# __PROGRAM____________________________________________________________________________________________________________
@settings(suppress_health_check=([HealthCheck.too_slow]))
@given(ticket=create_access_request_ticket())
def test_export_access_request_ticket(ticket, ticket_mdl_json_file, ticket_mdl_yaml_file):
    """A ticket should survive a dump-to-YAML then load-from-YAML round-trip."""
    # Dump model to JSON
    subject = ticket.subject
    assert ticket.subject == subject

    with open((ticket_mdl_json_file), "w") as file:
        data = ticket.model_dump(mode="json", by_alias=True)
        json.dump(data, file, indent=2)

    # Dump model to YAML
    dump_tickets(path=ticket_mdl_yaml_file, tickets=[ticket])

    # Load model from YAML
    imp_request = load_tickets(path=ticket_mdl_yaml_file)[0]

    assert imp_request == ticket


def test_schema_access_request_ticket(ticket_schema_file):
    export_schema(path=ticket_schema_file)
    assert (ticket_schema_file).exists()

    with open(ticket_schema_file) as schema:
        data = json.load(schema)
        assert type(data) is dict
        assert bool(data) is True


def test_schema_rejects_directory(tmp_path):
    """Passing a directory path to export_schema() should raise a ValueError."""
    with pytest.raises(ValueError, match="directory"):
        export_schema(path=tmp_path)


def test_schema_returns_dict_without_path():
    """Calling export_schema() without a path should return a JSON schema dict."""
    result = export_schema()
    assert isinstance(result, dict)
    assert result  # non-empty
