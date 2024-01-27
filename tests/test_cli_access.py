# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
import json

from typer.testing import CliRunner

from fwrqst.cli.main import cli

# __GLOBALS____________________________________________________________________________________________________________
runner = CliRunner()

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


# __PROGRAM____________________________________________________________________________________________________________
def test_schema_no_args_prints_to_stdout():
    """Without --output, the schema is printed to stdout."""
    result = runner.invoke(cli, ["schema", "accessrequest"])
    assert result.exit_code != EXIT_FAILURE
    # Output should contain JSON schema content
    assert "$defs" in result.stdout


def test_schema_output_to_file(ticket_schema_file):
    """Schema command writes a valid JSON schema file with expected structure."""
    result = runner.invoke(cli, ["schema", "accessrequest", "--output", str(ticket_schema_file)])
    assert result.exit_code == EXIT_SUCCESS
    assert ticket_schema_file.exists()

    with open(ticket_schema_file) as f:
        schema = json.load(f)

    assert isinstance(schema, dict)
    assert "$defs" in schema
