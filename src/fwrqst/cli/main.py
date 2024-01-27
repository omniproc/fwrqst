# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Root CLI application and subcommand registration.

This module assembles the top-level ``typer.Typer`` instance, registers
the three subcommand groups (``securechange``, ``schema``, ``config``),
and exposes the ``start()`` entry-point called by the console-script.
"""

# __IMPORTS______________________________________________________________________________________________________________
from typing import Annotated, Optional

import typer

from fwrqst import __program__, __version__
from fwrqst.cli import _stderr, _stdout
from fwrqst.cli.config import cli as fwrqst_config_cli
from fwrqst.cli.schema import cli as fwrqst_schema_cli
from fwrqst.cli.securechange import cli as tufin_securechange_cli

# --- CLI subcommand names -----------------------------------------------------------------
_SUBCOMMAND_SECURECHANGE = "securechange"
_SUBCOMMAND_SCHEMA = "schema"
_SUBCOMMAND_CONFIG = "config"


# __PROGRAM____________________________________________________________________________________________________________
def _version_callback(value: bool):
    """Print the program name and version, then exit."""
    if value:
        _stdout.print(f"{__program__} {__version__}")
        raise typer.Exit()


def _cli_callback(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show the program version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
):
    """Root callback — currently only handles the ``--version`` flag."""
    pass


cli = typer.Typer(
    rich_markup_mode="rich",
    epilog="A network blowtorch for SREs :fire:",
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    no_args_is_help=True,
    add_completion=True,
    callback=_cli_callback,
)
cli.add_typer(tufin_securechange_cli, name=_SUBCOMMAND_SECURECHANGE, help="Use Tufin's SecureChange API.")
cli.add_typer(fwrqst_schema_cli, name=_SUBCOMMAND_SCHEMA, help="Access this application's schema files.")
cli.add_typer(fwrqst_config_cli, name=_SUBCOMMAND_CONFIG, help="Manage this application's configuration.")


def start():
    """Console-script entry-point. Invokes the CLI and catches top-level exceptions."""
    try:
        cli()  # pragma: no cover
    except Exception as ex:
        _stderr.print(f"[bold red]{ex}[/bold red]")
        raise typer.Exit(code=1)
