# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
CLI subcommand for viewing and updating application configuration.

Exposes ``show``, ``find``, and ``set`` commands that read/write
the Dynaconf-backed settings stored in a platform-specific TOML file.
"""

# __IMPORTS______________________________________________________________________________________________________________
from typing import Annotated

import typer
from click import ParamType
from dynaconf import ValidationError
from rich.table import Table

from fwrqst.cli import _stderr, _stdout
from fwrqst.settings import locate, read, update

# __GLOBALS____________________________________________________________________________________________________________
cli = typer.Typer(
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    no_args_is_help=True,
)


# __PROGRAM____________________________________________________________________________________________________________
class Union:  # pragma: no cover
    """Wrapper type used by UnionParser to pass raw values through Typer's type system."""

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"<Union: value={self.value}>"


class UnionParser(ParamType):
    """Click parameter type that coerces string CLI input into ``str | int | bool``.

    Parsing rules (applied in order):
        1. Empty / ``None``  → ``None`` (resets the setting to its default).
        2. ``bool`` / ``int`` pass-through unchanged.
        3. String ``"true"`` / ``"false"`` (case-insensitive) → ``bool``.
        4. String parseable as ``int`` → ``int``.
        5. Anything else → ``str``.
    """

    name = "MANY"

    # Canonical boolean string literals recognised by this parser.
    _BOOL_TRUE = "true"
    _BOOL_FALSE = "false"

    def convert(self, value, param, ctx) -> str | int | bool | None:
        if not value:
            # No value given — return None so the setting resets to its default.
            return None
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return value
        elif isinstance(value, str):
            if value.lower() == self._BOOL_TRUE:
                return True
            elif value.lower() == self._BOOL_FALSE:
                return False
            try:
                return int(value)
            except ValueError:
                return value
        else:
            self.fail(f"{value!r} ({type(value).__name__}) is not a valid input type", param, ctx)


@cli.command()
def show():
    """
    Show current application configuration.
    """
    try:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Key")
        table.add_column("Value")
        table.add_column("Type")

        settings = read()
        for k, v in settings:
            table.add_row(k, str(v), str(type(v).__name__))

        _stdout.print(table)
    except ValidationError as ex:
        _stderr.print(f"[bold red]{ex} Please fix the error in your {locate()} file.[/bold red]")
        raise typer.Exit(code=1)


@cli.command()
def find():
    """
    Get settings file location on disk.
    """
    try:
        _stdout.print(locate())
    except Exception as ex:
        _stderr.print(f"[bold red]{ex}[/bold red]")
        raise typer.Exit(code=1)


@cli.command(no_args_is_help=True)
def set(
    key: Annotated[
        str,
        typer.Option("--key", "-k", help="Setting to configure."),
    ] = None,  # type: ignore[assignment]
    value: Annotated[
        Union,
        typer.Option(
            "--value",
            "-v",
            help="Value of the setting. Empty sets default.",
            click_type=UnionParser(),
        ),
    ] = None,  # type: ignore[assignment]
):
    """
    Set and persist a setting to disk.
    """
    try:
        update(key=key, value=value, save=True)
        _stdout.print(f"[bold green]{key}[/bold green] saved to {locate()}")
    except Exception as ex:
        _stderr.print(f"[bold red]{ex}[/bold red]")
        raise typer.Exit(code=1)
