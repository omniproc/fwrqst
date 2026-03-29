# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
FwRst 🔥 - A small tool to ease big pain
"""

# __IMPORTS______________________________________________________________________________________________________________
from importlib.metadata import PackageNotFoundError, version

__program__ = "fwrqst"
__author__ = "Robert Ruf"
__email__ = "fwrqst.hvgh7@silomails.com"
__copyright__ = "Copyright 2024, Robert Ruf"
__license__ = "MIT"


# Version number is automatically set at build time by setuptools_scm and only available via package metadata
# We could make setuptools_scm write the calculated version into a separate file that we read from
# but we don't see any benefit in that approach, so we opt to not hardcode the version number into a file.
try:
    __version__ = version(__program__)
except PackageNotFoundError:  # pragma: no cover
    # package is not installed
    pass

from fwrqst.settings import SETTINGS

__all__ = [
    "__program__",
    "__author__",
    "__email__",
    "__copyright__",
    "__license__",
    "__version__",
    "SETTINGS",
]
