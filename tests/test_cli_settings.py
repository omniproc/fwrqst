# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as hsettings
from hypothesis import strategies as st
from typer.testing import CliRunner

from fwrqst import __program__
from fwrqst.cli.main import cli
from fwrqst.models.types import Priority
from fwrqst.settings import (
    _DYNACONF_SETTINGS_FILE,
    KEY_ACCESS_REQUEST_EXPIRATION_DAYS,
    KEY_ACCESS_REQUEST_PRIORITY,
    KEY_ACCESS_REQUEST_SUBJECT,
    KEY_SECURE_CHANGE_PORT,
    SETTINGS,
)

# __GLOBALS____________________________________________________________________________________________________________
runner = CliRunner()

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

# Source-of-truth: valid settings keys from the application
_ALL_VALID_KEYS = list(SETTINGS.as_dict().keys())


# __PROGRAM____________________________________________________________________________________________________________
def test_version():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == EXIT_SUCCESS
    assert __program__ in result.stdout


def test_find():
    result = runner.invoke(cli, ["config", "find"])
    assert result.exit_code == EXIT_SUCCESS
    assert _DYNACONF_SETTINGS_FILE in result.stdout


def test_show():
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == EXIT_SUCCESS
    # All known settings keys should appear in the output (Rich may truncate long names)
    for key in _ALL_VALID_KEYS:
        assert key[:20] in result.stdout


def test_set_invalid_key(mocker):
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", "NONEXISTENT_KEY_XYZ", "-v", "anything"])
    assert result.exit_code == EXIT_FAILURE


# Strategy for strings that won't be parsed as numbers or booleans by UnionParser
_cli_safe_text = st.text(
    alphabet=st.characters(codec="utf-8", categories=("L",)),
    min_size=1,
    max_size=30,
).filter(lambda s: s.lower() not in ("true", "false"))


@hsettings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(value=_cli_safe_text)
def test_set_string_setting(value, mocker):
    """Setting a string config key with any non-empty string should succeed."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_ACCESS_REQUEST_SUBJECT, "-v", value])
    assert result.exit_code == EXIT_SUCCESS


@hsettings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(value=st.integers(min_value=1, max_value=65535))
def test_set_port_setting(value, mocker):
    """Setting an integer config key with valid integers should succeed."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_SECURE_CHANGE_PORT, "-v", str(value)])
    assert result.exit_code == EXIT_SUCCESS


def test_set_port_rejects_string(mocker):
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_SECURE_CHANGE_PORT, "-v", "not_a_number"])
    assert result.exit_code == EXIT_FAILURE


@hsettings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(priority=st.sampled_from(Priority))
def test_set_valid_priority(priority, mocker):
    """Setting priority to any valid Priority enum value should succeed."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_ACCESS_REQUEST_PRIORITY, "-v", priority.value])
    assert result.exit_code == EXIT_SUCCESS


def test_set_invalid_priority(mocker):
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_ACCESS_REQUEST_PRIORITY, "-v", "URGENT"])
    assert result.exit_code == EXIT_FAILURE


@hsettings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(days=st.integers(min_value=1, max_value=365))
def test_set_expiration_days(days, mocker):
    """Setting expiration days to any value in [1, 365] should succeed."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_ACCESS_REQUEST_EXPIRATION_DAYS, "-v", str(days)])
    assert result.exit_code == EXIT_SUCCESS


def test_set_boolean_true(mocker):
    """UnionParser should parse 'true' string as boolean True."""
    mocker.patch("fwrqst.settings.persist")
    # ACCESS_REQUEST_SUBJECT expects a string, but UnionParser converts "true" -> True (bool).
    # Dynaconf should reject a bool for a string-typed setting.
    result = runner.invoke(cli, ["config", "set", "-k", KEY_ACCESS_REQUEST_SUBJECT, "-v", "true"])
    assert result.exit_code == EXIT_FAILURE


def test_set_boolean_false(mocker):
    """UnionParser should parse 'false' string as boolean False."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_ACCESS_REQUEST_SUBJECT, "-v", "false"])
    assert result.exit_code == EXIT_FAILURE


def test_set_integer_value_for_int_key(mocker):
    """UnionParser should parse numeric string as int; valid for int-typed keys."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_SECURE_CHANGE_PORT, "-v", "8080"])
    assert result.exit_code == EXIT_SUCCESS


def test_set_no_value_resets_default(mocker):
    """Calling set without a -v value should reset the setting to its default."""
    mocker.patch("fwrqst.settings.persist")
    result = runner.invoke(cli, ["config", "set", "-k", KEY_SECURE_CHANGE_PORT])
    assert result.exit_code == EXIT_SUCCESS


def test_start_exception_handling(mocker):
    """start() should catch exceptions and exit with code 1."""
    mocker.patch("fwrqst.cli.main.cli", side_effect=RuntimeError("test error"))
    import typer

    from fwrqst.cli.main import start

    with pytest.raises(typer.Exit) as exc_info:
        start()
    assert exc_info.value.exit_code == 1


# __UnionParser direct tests_______________________________________________________________________________________________
class TestUnionParser:
    """Direct tests for UnionParser.convert() branches."""

    def setup_method(self):
        from fwrqst.cli.config import UnionParser

        self.parser = UnionParser()

    def test_none_value_returns_none(self):
        assert self.parser.convert(None, None, None) is None

    def test_empty_string_returns_none(self):
        assert self.parser.convert("", None, None) is None

    def test_bool_passthrough(self):
        assert self.parser.convert(True, None, None) is True
        assert self.parser.convert(False, None, None) is None  # False is falsy → returns None

    def test_int_passthrough(self):
        assert self.parser.convert(42, None, None) == 42

    def test_unsupported_type_fails(self):
        with pytest.raises(Exception):
            self.parser.convert(3.14, None, None)


# __show/find error paths__________________________________________________________________________________________________
def test_show_validation_error(mocker):
    """show command should handle ValidationError gracefully."""
    from dynaconf import ValidationError

    mocker.patch("fwrqst.cli.config.read", side_effect=ValidationError("bad config"))
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == EXIT_FAILURE


def test_find_exception(mocker):
    """find command should handle exceptions gracefully."""
    mocker.patch("fwrqst.cli.config.locate", side_effect=RuntimeError("disk error"))
    result = runner.invoke(cli, ["config", "find"])
    assert result.exit_code == EXIT_FAILURE
