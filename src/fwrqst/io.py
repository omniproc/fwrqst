# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
File I/O helpers for reading/writing tickets in YAML and exporting JSON schemas.

All public functions operate on ``pathlib.Path`` objects and raise on
invalid input rather than returning sentinel values.
"""

# __IMPORTS______________________________________________________________________________________________________________
import json
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from fwrqst.models.ticket import AccessRequestTicket, AccessRequestTickets


# __PROGRAM______________________________________________________________________________________________________________
def load_tickets(path: Path) -> list[AccessRequestTicket]:
    """
    Load access request tickets from a YAML file.
    """
    data = read_yaml(path)
    tickets = AccessRequestTickets.model_validate(data)
    return tickets.root


def dump_tickets(path: Path, tickets: list[AccessRequestTicket]) -> None:
    """
    Dump access request tickets to a YAML file.
    """
    model = AccessRequestTickets(root=tickets)
    data = model.model_dump(mode="json")
    write_yaml(path, data)


def read_yaml(path: Path) -> dict:
    """
    Read a YAML file and return its contents as a dict.
    """
    with open(path, "r") as file:
        return yaml.safe_load(file)


def write_yaml(path: Path, data: dict) -> None:
    """
    Write a dict to a YAML file.
    """
    with open(path, "w") as file:
        yaml.dump(data, file)


def export_schema(path: Path = None) -> None | dict:
    """
    Returns the JSON schema of access request tickets.
    If a path is provided, saves the schema to the file.
    """
    adapter = TypeAdapter(AccessRequestTickets)
    if not path:
        return adapter.json_schema()

    if path.is_dir():
        raise ValueError("Provided path is a directory, expected a file path.")
    path = path.with_suffix(".json")
    with open(path, "w") as file:
        file.write(json.dumps(adapter.json_schema(), indent=2))
