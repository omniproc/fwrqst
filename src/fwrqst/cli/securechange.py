# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
CLI subcommand for Tufin SecureChange ticket operations (create / read / cancel).

Shared connection parameters (domain, port, credentials, …) are collected
by the ``@cli.callback`` and forwarded to every child command via the
Typer context object.
"""

# __IMPORTS______________________________________________________________________________________________________________
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Optional

import typer
from httpx import HTTPStatusError, RequestError

from fwrqst.api.securechange import AccessRequestService
from fwrqst.cli import _stderr
from fwrqst.io import load_tickets
from fwrqst.settings import (
    KEY_ACCESS_REQUEST_WORKFLOW,
    KEY_SECURE_CHANGE_CA_FILE,
    KEY_SECURE_CHANGE_DOMAIN,
    KEY_SECURE_CHANGE_PORT,
    SETTINGS,
    update,
)

# --- Environment variable names exposed to the shell -----------------------------------
_ENV_USERNAME = "FWRQST_SECURE_CHANGE_USERNAME"
_ENV_PASSWORD = "FWRQST_SECURE_CHANGE_PASSWORD"  # nosec B105
_ENV_DOMAIN = "FWRQST_SECURE_CHANGE_DOMAIN"
_ENV_PORT = "FWRQST_SECURE_CHANGE_PORT"
_ENV_CA_FILE = "FWRQST_SECURE_CHANGE_CA_FILE"
_ENV_WORKFLOW = "FWRQST_ACCESS_REQUEST_WORKFLOW"

# --- CLI context dict keys ----------------------------------------------------------------
_CTX_DOMAIN = "domain"
_CTX_PORT = "port"
_CTX_CAFILE = "cafile"
_CTX_WORKFLOW = "workflow"
_CTX_SERVICE = "service"

# __GLOBALS____________________________________________________________________________________________________________
cli = typer.Typer(
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    no_args_is_help=True,
)


# __VALIDATORS_________________________________________________________________________________________________________
def _fallback_to_default(ctx: typer.Context, param: typer.CallbackParam, value: str):
    """Return *value* when truthy, otherwise the parameter's default, or raise if neither exists."""
    _default = param.default
    if value:
        return value
    elif _default:
        return _default
    else:
        raise typer.BadParameter(f"{param.name} is required.")


# __PROGRAM____________________________________________________________________________________________________________
# NOTE: Shared params are currently required to display the help of the subcommands.
# This is a known Typer limitation: https://github.com/tiangolo/typer/issues/153


@contextmanager
def _handle_api_errors(operation: str):
    """Catch ``httpx`` transport and HTTP errors, print a Rich-formatted message, and exit."""
    try:
        yield
    except HTTPStatusError as ex:
        _stderr.print(
            f"[bold red]Failed to {operation}. HTTP status code: {ex.response.status_code}.\n{ex.response.text}[/bold red]"
        )
        raise typer.Exit(code=1)
    except RequestError as ex:
        _stderr.print(f"[bold red]Failed to {operation}.\n{ex}[/bold red]")
        raise typer.Exit(code=1)


@cli.callback(no_args_is_help=True)
def securechange_callback(
    ctx: typer.Context,
    username: Annotated[
        Optional[str],
        typer.Option(
            "-u",
            "--username",
            envvar=_ENV_USERNAME,
            help="Username to authenticate with the provided domain.",
        ),
    ],
    password: Annotated[
        Optional[str],
        typer.Option(
            "-p",
            "--password",
            envvar=_ENV_PASSWORD,
            help="Password to authenticate with the provided domain.",
            prompt=True,
            confirmation_prompt=False,
            hide_input=True,
        ),
    ],
    domain: Annotated[
        Optional[str],
        typer.Option(
            "-d",
            "--domain",
            callback=_fallback_to_default,
            envvar=_ENV_DOMAIN,
            help="The Tufin secure change base domain.",
        ),
    ] = SETTINGS.get(KEY_SECURE_CHANGE_DOMAIN, None),
    port: Annotated[
        Optional[int],
        typer.Option(
            "--port",
            callback=_fallback_to_default,
            envvar=_ENV_PORT,
            help="The Tufin secure change API port.",
        ),
    ] = SETTINGS.get(KEY_SECURE_CHANGE_PORT, None),
    cafile: Annotated[
        Optional[Path],
        typer.Option(
            "-c",
            "--cafile",
            envvar=_ENV_CA_FILE,
            help="Path to the CA file (PEM) to trust when connecting to the provided domain.",
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    workflow: Annotated[
        Optional[str],
        typer.Option(
            "--workflow",
            callback=_fallback_to_default,
            envvar=_ENV_WORKFLOW,
            help="The Tufin secure change workflow to use.",
        ),
    ] = SETTINGS.get(KEY_ACCESS_REQUEST_WORKFLOW, None),
):
    """Collect shared connection parameters and initialise the API service."""
    cli_context = ctx.ensure_object(dict)

    # Override settings with higher-precedence CLI args for the current run.
    # Each call to update() also triggers Dynaconf validation.
    if domain:
        cli_context[_CTX_DOMAIN] = domain
        update(key=KEY_SECURE_CHANGE_DOMAIN, value=str(domain))
    if port:
        cli_context[_CTX_PORT] = port
        update(key=KEY_SECURE_CHANGE_PORT, value=port)
    if cafile:
        cli_context[_CTX_CAFILE] = cafile
        update(key=KEY_SECURE_CHANGE_CA_FILE, value=str(cafile))
    if workflow:
        cli_context[_CTX_WORKFLOW] = workflow
        update(key=KEY_ACCESS_REQUEST_WORKFLOW, value=workflow)

    # Initialise the service shared by all child commands.
    try:
        if not username or not password:
            raise ValueError("Username and password are required.")
        service = AccessRequestService(username=username, password=password, domain=domain, port=port, cafile=cafile)
        cli_context[_CTX_SERVICE] = service
    except Exception as ex:
        _stderr.print(f"[bold red]Failed to create AccessRequestService.\n{ex} Verify the provided settings.[/bold red]")
        raise typer.Exit(code=1)


@cli.command(no_args_is_help=True)
def create(
    ctx: typer.Context,
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Path to a Tufin access request file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
):
    """Create a new Tufin access request from a valid request input file."""
    try:
        tickets = load_tickets(path=input_file)
    except Exception as ex:
        _stderr.print(f"[bold red]Failed to load Tufin access request from file '{input_file}'.\n{ex}[/bold red]")
        raise typer.Exit(code=1)

    with _handle_api_errors("create Tufin access request"):
        ctx.obj[_CTX_SERVICE].create_ticket(ticket=tickets)


@cli.command(no_args_is_help=True)
def read(
    ctx: typer.Context,
    ticket_id: Annotated[str, typer.Argument(help="The Tufin access request ID.")],
    output: Annotated[
        Optional[Path],
        typer.Option(help="Path to an output file.", file_okay=True, dir_okay=False, writable=True),
    ] = None,
):
    """Read an existing Tufin access request."""
    with _handle_api_errors("read Tufin access request"):
        ctx.obj[_CTX_SERVICE].get_ticket(ticket_id=ticket_id)


@cli.command(no_args_is_help=True)
def cancel(
    ctx: typer.Context,
    ticket_id: Annotated[str, typer.Argument(help="The Tufin access request ID.")],
):
    """Cancel a pending Tufin access request."""
    with _handle_api_errors("cancel Tufin access request"):
        ctx.obj[_CTX_SERVICE].cancel_ticket(ticket_id=ticket_id)
