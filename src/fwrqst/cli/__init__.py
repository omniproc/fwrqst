# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Command-line interface (CLI) package.

Requires the ``[cli]`` install extra (typer + rich).  A missing
dependency triggers an immediate, user-friendly error message.
"""

# __IMPORTS______________________________________________________________________________________________________________
try:
    # Fail early. This package can only be used if the CLI option was installed.
    import typer
    from rich.console import Console
except ImportError:  # pragma: no cover
    raise SystemExit("You did not install FwRqst with the CLI option. Please install it using 'pip install fwrqst[cli]'.")


# __GLOBALS____________________________________________________________________________________________________________
# Shared Rich consoles used by every CLI subcommand for consistent output.
_stdout = Console()  # normal output
_stderr = Console(stderr=True)  # error / diagnostic output
