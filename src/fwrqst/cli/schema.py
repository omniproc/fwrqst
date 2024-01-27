# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
CLI subcommand for exporting the JSON schema of access request tickets.
"""

# __IMPORTS______________________________________________________________________________________________________________
from pathlib import Path
from typing import Annotated

import typer

from fwrqst.cli import _stdout
from fwrqst.io import export_schema

# __GLOBALS____________________________________________________________________________________________________________
cli = typer.Typer(
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    no_args_is_help=True,
)


@cli.command()
def accessrequest(
    ctx: typer.Context,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Path to an output file.", file_okay=True, dir_okay=False, writable=True),
    ] = None,
):
    """
    Get the Tufin SecureChange access request schema.
    """
    if output:
        export_schema(path=output)
    else:
        _stdout.print(export_schema())
