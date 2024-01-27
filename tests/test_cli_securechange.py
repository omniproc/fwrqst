# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from fwrqst.cli.main import cli

# __GLOBALS____________________________________________________________________________________________________________
runner = CliRunner()

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

_VALID_DOMAIN = "tufin.example.com"
_VALID_USERNAME = "testuser"
_VALID_PASSWORD = "testpass"  # nosec B105
_VALID_PORT = "443"
_VALID_WORKFLOW = "Standard"

# Shared CLI args that are needed for the securechange callback
_SHARED_ARGS = [
    "securechange",
    "-u",
    _VALID_USERNAME,
    "-p",
    _VALID_PASSWORD,
    "-d",
    _VALID_DOMAIN,
    "--port",
    _VALID_PORT,
    "--workflow",
    _VALID_WORKFLOW,
]


# __HELPERS____________________________________________________________________________________________________________
def _mock_service():
    """Create a mock AccessRequestService."""
    svc = MagicMock()
    svc.get_ticket.return_value = MagicMock()
    svc.create_ticket.return_value = "12345"
    svc.cancel_ticket.return_value = None
    return svc


# __PROGRAM____________________________________________________________________________________________________________
def test_securechange_no_args_shows_help():
    """Calling securechange without args should show help."""
    result = runner.invoke(cli, ["securechange"])
    assert result.exit_code != EXIT_FAILURE or "--help" in result.stdout or "Usage" in result.stdout


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_uses_settings_default_for_workflow(mock_svc_cls):
    """When --workflow is passed empty, _fallback_to_default should fall back to the SETTINGS default."""
    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    # Pass empty --workflow to trigger the elif _default branch in _fallback_to_default
    args_with_empty_workflow = [
        "securechange",
        "-u",
        _VALID_USERNAME,
        "-p",
        _VALID_PASSWORD,
        "-d",
        _VALID_DOMAIN,
        "--port",
        _VALID_PORT,
        "--workflow",
        "",
        "read",
        "999999",
    ]
    result = runner.invoke(cli, args_with_empty_workflow)
    assert result.exit_code == EXIT_SUCCESS


@patch("fwrqst.cli.securechange.update")
@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_with_cafile(mock_svc_cls, mock_update, tmp_path):
    """Passing --cafile should set the CA file in context and settings."""
    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    ca_file = tmp_path / "ca.pem"
    ca_file.write_text("CERT")

    result = runner.invoke(
        cli,
        [*_SHARED_ARGS, "-c", str(ca_file), "read", "999999"],
    )
    assert result.exit_code == EXIT_SUCCESS


def test_securechange_missing_domain():
    """Missing required domain should fail with exit code != 0."""
    result = runner.invoke(
        cli,
        [
            "securechange",
            "-u",
            _VALID_USERNAME,
            "-p",
            _VALID_PASSWORD,
            "-d",
            "",
            "--port",
            _VALID_PORT,
            "read",
            "123",
        ],
        input="\n",
    )
    assert result.exit_code != EXIT_SUCCESS


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_read_ticket(mock_svc_cls):
    """Read command should invoke get_ticket on the service."""
    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    result = runner.invoke(cli, [*_SHARED_ARGS, "read", "999999"])
    assert result.exit_code == EXIT_SUCCESS
    mock_svc.get_ticket.assert_called_once_with(ticket_id="999999")


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_cancel_ticket(mock_svc_cls):
    """Cancel command should invoke cancel_ticket on the service."""
    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    result = runner.invoke(cli, [*_SHARED_ARGS, "cancel", "999999"])
    assert result.exit_code == EXIT_SUCCESS
    mock_svc.cancel_ticket.assert_called_once_with(ticket_id="999999")


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_create_ticket(mock_svc_cls, tmp_path):
    """Create command should load YAML and call create_ticket."""
    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    _expiration = (date.today() + timedelta(days=30)).isoformat()
    yaml_content = f"""
- subject: Test Ticket
  workflow: Standard
  priority: Normal
  expiration: '{_expiration}'
  access_requests:
    - comment: Rule 1
      action: accept
      source_domain: Default
      sources:
        - kind: IP
          address: 10.0.0.1
          cidr: 32
      destination_domain: Default
      destinations:
        - kind: DNS
          fqdn: example.com
      services:
        - protocol: TCP
          port: 443
"""
    input_file = tmp_path / "request.yaml"
    input_file.write_text(yaml_content)

    result = runner.invoke(cli, [*_SHARED_ARGS, "create", str(input_file)])
    assert result.exit_code == EXIT_SUCCESS
    mock_svc.create_ticket.assert_called_once()


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_create_invalid_file(mock_svc_cls, tmp_path):
    """Create command should fail gracefully with invalid YAML content."""
    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    input_file = tmp_path / "bad.yaml"
    input_file.write_text("not: valid: access: request")

    result = runner.invoke(cli, [*_SHARED_ARGS, "create", str(input_file)])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_controller_init_failure(mock_svc_cls):
    """When service initialization fails, should exit with code 1."""
    mock_svc_cls.side_effect = RuntimeError("Connection failed")

    result = runner.invoke(cli, [*_SHARED_ARGS, "read", "123"])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_read_http_error(mock_svc_cls):
    """Read command should handle HTTPStatusError gracefully."""
    from httpx import HTTPStatusError, Request, Response

    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    response = Response(status_code=404, text="Not Found", request=Request("GET", "https://example.com"))
    mock_svc.get_ticket.side_effect = HTTPStatusError("Not Found", request=response.request, response=response)

    result = runner.invoke(cli, [*_SHARED_ARGS, "read", "999999"])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_read_request_error(mock_svc_cls):
    """Read command should handle RequestError gracefully."""
    from httpx import RequestError

    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc
    mock_svc.get_ticket.side_effect = RequestError("Connection refused")

    result = runner.invoke(cli, [*_SHARED_ARGS, "read", "999999"])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_cancel_http_error(mock_svc_cls):
    """Cancel command should handle HTTPStatusError gracefully."""
    from httpx import HTTPStatusError, Request, Response

    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    response = Response(status_code=400, text="Bad Request", request=Request("PUT", "https://example.com"))
    mock_svc.cancel_ticket.side_effect = HTTPStatusError("Bad Request", request=response.request, response=response)

    result = runner.invoke(cli, [*_SHARED_ARGS, "cancel", "999999"])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_cancel_request_error(mock_svc_cls):
    """Cancel command should handle RequestError gracefully."""
    from httpx import RequestError

    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc
    mock_svc.cancel_ticket.side_effect = RequestError("Connection refused")

    result = runner.invoke(cli, [*_SHARED_ARGS, "cancel", "999999"])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_create_http_error(mock_svc_cls, tmp_path):
    """Create command should handle HTTPStatusError gracefully."""
    from httpx import HTTPStatusError, Request, Response

    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc

    response = Response(status_code=500, text="Internal Server Error", request=Request("POST", "https://example.com"))
    mock_svc.create_ticket.side_effect = HTTPStatusError("Error", request=response.request, response=response)

    _expiration = (date.today() + timedelta(days=30)).isoformat()
    input_file = tmp_path / "request.yaml"
    input_file.write_text(
        f"""
- subject: Test
  workflow: Standard
  priority: Normal
  expiration: '{_expiration}'
  access_requests:
    - comment: Rule 1
      action: accept
      source_domain: Default
      sources:
        - kind: IP
          address: 10.0.0.1
          cidr: 32
      destination_domain: Default
      destinations:
        - kind: DNS
          fqdn: example.com
      services:
        - protocol: TCP
          port: 443
"""
    )

    result = runner.invoke(cli, [*_SHARED_ARGS, "create", str(input_file)])
    assert result.exit_code == EXIT_FAILURE


@patch("fwrqst.cli.securechange.AccessRequestService")
def test_securechange_create_request_error(mock_svc_cls, tmp_path):
    """Create command should handle RequestError gracefully."""
    from httpx import RequestError

    mock_svc = _mock_service()
    mock_svc_cls.return_value = mock_svc
    mock_svc.create_ticket.side_effect = RequestError("Connection refused")

    _expiration = (date.today() + timedelta(days=30)).isoformat()
    input_file = tmp_path / "request.yaml"
    input_file.write_text(
        f"""
- subject: Test
  workflow: Standard
  priority: Normal
  expiration: '{_expiration}'
  access_requests:
    - comment: Rule 1
      action: accept
      source_domain: Default
      sources:
        - kind: IP
          address: 10.0.0.1
          cidr: 32
      destination_domain: Default
      destinations:
        - kind: DNS
          fqdn: example.com
      services:
        - protocol: TCP
          port: 443
"""
    )

    result = runner.invoke(cli, [*_SHARED_ARGS, "create", str(input_file)])
    assert result.exit_code == EXIT_FAILURE
