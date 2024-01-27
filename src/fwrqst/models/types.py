# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Various ENUMs used by different models
"""

# __IMPORTS______________________________________________________________________________________________________________
from enum import StrEnum, unique


# __MODEL________________________________________________________________________________________________________________
@unique
class ServiceType(StrEnum):
    """Classification of a Tufin service definition."""

    PROTOCOL = "PROTOCOL"
    PREDEFINED = "PREDEFINED"


@unique
class ProtocolType(StrEnum):
    """
    A network protocol
    """

    TCP = "TCP"
    UDP = "UDP"


@unique
class Priority(StrEnum):
    """
    A Tufin ticket priority
    """

    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    CRITICAL = "Critical"


@unique
class EndpointType(StrEnum):
    """
    A Tufin endpoint type
    """

    ANY = "ANY"
    IP = "IP"
    DNS = "DNS"
    RANGE = "RANGE"
    OBJECT = "Object"


@unique
class Action(StrEnum):
    """
    A Tufin access request action
    """

    ACCEPT = "accept"
    DROP = "drop"
    REMOVE = "remove"


@unique
class RequestType(StrEnum):
    """
    A Tufin access request type
    """

    MULTI_ACCESS_REQUEST = "multi_access_request"
