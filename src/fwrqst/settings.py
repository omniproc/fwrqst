# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Application configuration powered by Dynaconf.

Settings are loaded from a TOML file in the platform-specific user config
directory, overridable by environment variables prefixed with ``FWRQST_``.
This module exposes canonical key-name constants (``KEY_*``) so that every
SETTINGS.get() call across the codebase references a single source of truth.
"""

# __IMPORTS______________________________________________________________________________________________________________
from pathlib import Path
from types import UnionType
from typing import Any

from dynaconf import Dynaconf, ValidationError, Validator, loaders
from dynaconf.utils.boxing import DynaBox
from platformdirs import user_config_dir

from fwrqst import __program__

# __GLOBALS______________________________________________________________________________________________________________
_DYNACONF_ENVVAR_PREFIX: str = "FWRQST"
_DYNACONF_SETTINGS_FILE = "settings.toml"
_USER_CONFIGURATION_DIR = user_config_dir(appname=__program__)
# Create the platform config directory if it doesn't already exist
Path(_USER_CONFIGURATION_DIR).mkdir(parents=True, exist_ok=True)
_DYNACONF_SETTINGS_LOCATION = Path(_USER_CONFIGURATION_DIR) / _DYNACONF_SETTINGS_FILE

# Allowed priority values for Tufin access request tickets.
# Must stay in sync with fwrqst.models.types.Priority.
_PRIORITIES = ["Low", "Normal", "High", "Critical"]

# Maximum amount of expiration days accepted by Tufin for a new Access Request
_DEFAULT_ACCESS_REQUEST_MAX_EXPIRATION_DAYS: int = 365
_DEFAULT_ACCESS_REQUEST_EXPIRATION_DAYS: int = _DEFAULT_ACCESS_REQUEST_MAX_EXPIRATION_DAYS

_DEFAULT_ACCESS_REQUEST_PRIORITY: str = _PRIORITIES[1]
_DEFAULT_ACCESS_REQUEST_SUBJECT: str = "FwRqst"

# Default Tufin domain to process an access request for
_DEFAULT_ACCESS_REQUEST_DOMAIN = "Default"
# Default Tufin workflow to pass the access request to
_DEFAULT_ACCESS_REQUEST_WORKFLOW = "Standard"

# Default Tufin API port and host
_DEFAULT_SECURE_CHANGE_PORT = 443
_DEFAULT_SECURE_CHANGE_DOMAIN = ""
_DEFAULT_SECURE_CHANGE_API_BASE_PATH = "/securechangeworkflow/api/securechange/"
_DEFAULT_SECURE_CHANGE_CA_FILE = ""

# --- Settings key names -----------------------------------------------------------------------
# Canonical names for every configuration key.  Used for Dynaconf validator
# registrations, SETTINGS.get() look-ups, and CLI / model references.
# Centralising these eliminates duplicated string literals across the codebase.
KEY_ACCESS_REQUEST_MAX_EXPIRATION_DAYS = "ACCESS_REQUEST_MAX_EXPIRATION_DAYS"
KEY_ACCESS_REQUEST_EXPIRATION_DAYS = "ACCESS_REQUEST_EXPIRATION_DAYS"
KEY_ACCESS_REQUEST_SUBJECT = "ACCESS_REQUEST_SUBJECT"
KEY_ACCESS_REQUEST_PRIORITY = "ACCESS_REQUEST_PRIORITY"
KEY_ACCESS_REQUEST_DOMAIN = "ACCESS_REQUEST_DOMAIN"
KEY_ACCESS_REQUEST_WORKFLOW = "ACCESS_REQUEST_WORKFLOW"
KEY_SECURE_CHANGE_DOMAIN = "SECURE_CHANGE_DOMAIN"
KEY_SECURE_CHANGE_PORT = "SECURE_CHANGE_PORT"
KEY_SECURE_CHANGE_API_BASE_PATH = "SECURE_CHANGE_API_BASE_PATH"
KEY_SECURE_CHANGE_CA_FILE = "SECURE_CHANGE_CA_FILE"

# __PROGRAM______________________________________________________________________________________________________________
SETTINGS = Dynaconf(
    envvar_prefix=_DYNACONF_ENVVAR_PREFIX,
    root_path=_USER_CONFIGURATION_DIR,
    settings_files=[_DYNACONF_SETTINGS_FILE],
    apply_default_on_none=True,
    validate_on_update=True,
)


def persist() -> None:  # pragma: no cover
    """Write the current in-memory settings to the TOML file on disk."""
    loaders.write(
        str(_DYNACONF_SETTINGS_LOCATION),
        DynaBox(SETTINGS.as_dict()).to_dict(),
        merge=False,
    )


def locate() -> Path:
    """Return the absolute path to the TOML settings file on disk."""
    return _DYNACONF_SETTINGS_LOCATION


def validate() -> None:
    """Run all registered validators.  Raises ``dynaconf.ValidationError`` on failure."""
    SETTINGS.validators.validate()


def update(key: str, value: Any, save: bool = False) -> None:
    """Update a single setting by *key*.

    The new *value* is validated immediately (``validate_on_update=True``).
    If validation fails the previous value is restored and the exception
    is re-raised.  When *save* is ``True`` the change is also persisted
    to the TOML file on disk.

    Raises:
        KeyError: If *key* does not match any registered setting.
    """
    keys = [key.upper() for key in SETTINGS.as_dict().keys()]
    if key.upper() in keys:
        previous = SETTINGS[key]
        try:
            SETTINGS.update({key: value})
            # Not needed since we use validate_on_update=True
            # SETTINGS.validators.validate()
            if save:
                persist()
        except Exception as ex:
            SETTINGS[key] = previous
            raise ex
    else:
        raise KeyError(f"Setting '{key}' not found.")


def read() -> list[tuple[str, Any]]:
    """Return all settings as ``(key, value)`` pairs after validation."""
    validate()
    items: list[tuple[str, Any]] = list(SETTINGS.as_dict().items())
    return items


def file_path_exists(value: str | None) -> bool:
    """Check whether *value* points to an existing file.

    Returns ``True`` when *value* is ``None`` or empty (nothing to validate)
    or when the path resolves to an existing file.  Returns ``False`` for
    any non-existent or invalid path.
    """
    if value:
        try:
            return Path(value).is_file()
        except Exception:
            return False
    return True


def _typed_validator(name: str, expected_type: type | UnionType, default, **constraint_kwargs) -> list[Validator]:
    """Create a pair of Dynaconf validators for a single setting.

    Returns two ``Validator`` instances:
        1. **Type validator** — rejects values that are not ``expected_type``.
        2. **Constraint validator** — sets the *default* and enforces any
           additional rules (``gte``, ``len_min``, ``is_in``, …) passed
           via *constraint_kwargs*.
    """
    return [
        Validator(
            name,
            is_type_of=expected_type,
            messages={"operations": "{name} must be type of {op_value} but is '{value}'."},
        ),
        Validator(
            name,
            default=default,
            messages={"operations": "{name} must be set to a value."},
            **constraint_kwargs,
        ),
    ]


# Register Dynaconf validators for every setting.
# Each _typed_validator() call produces two validators: one checks the type,
# the other applies constraint rules (min value, allowed values, etc.) and
# populates a default when the setting is absent.
SETTINGS.validators.register(
    *_typed_validator(
        KEY_ACCESS_REQUEST_MAX_EXPIRATION_DAYS,
        int | None,
        _DEFAULT_ACCESS_REQUEST_MAX_EXPIRATION_DAYS,
        gte=1,
    ),
    *_typed_validator(
        KEY_ACCESS_REQUEST_EXPIRATION_DAYS,
        int | None,
        _DEFAULT_ACCESS_REQUEST_EXPIRATION_DAYS,
        gte=1,
    ),
    *_typed_validator(
        KEY_ACCESS_REQUEST_SUBJECT,
        str | None,
        _DEFAULT_ACCESS_REQUEST_SUBJECT,
        len_min=1,
    ),
    *_typed_validator(
        KEY_ACCESS_REQUEST_PRIORITY,
        str | None,
        _DEFAULT_ACCESS_REQUEST_PRIORITY,
        is_in=_PRIORITIES,
    ),
    *_typed_validator(
        KEY_ACCESS_REQUEST_DOMAIN,
        str | None,
        _DEFAULT_ACCESS_REQUEST_DOMAIN,
        len_min=1,
    ),
    *_typed_validator(
        KEY_ACCESS_REQUEST_WORKFLOW,
        str | None,
        _DEFAULT_ACCESS_REQUEST_WORKFLOW,
        len_min=1,
        must_exist=True,
    ),
    *_typed_validator(
        KEY_SECURE_CHANGE_DOMAIN,
        str | None,
        _DEFAULT_SECURE_CHANGE_DOMAIN,
        must_exist=True,
    ),
    # SECURE_CHANGE_PORT only needs a type check and a default — no constraint pair.
    Validator(
        KEY_SECURE_CHANGE_PORT,
        is_type_of=int | None,
        default=_DEFAULT_SECURE_CHANGE_PORT,
        messages={"operations": "{name} must be type of {op_value} but is '{value}'."},
    ),
    *_typed_validator(
        KEY_SECURE_CHANGE_API_BASE_PATH,
        str | None,
        _DEFAULT_SECURE_CHANGE_API_BASE_PATH,
        must_exist=True,
    ),
    # SECURE_CHANGE_CA_FILE uses two standalone validators: a type check and a
    # file-existence condition, since _typed_validator doesn't support condition=.
    Validator(
        KEY_SECURE_CHANGE_CA_FILE,
        is_type_of=str | None,
        messages={
            "operations": ("{name} must be type of {op_value} but is '{value}'."),
        },
    ),
    Validator(
        KEY_SECURE_CHANGE_CA_FILE,
        must_exist=True,
        default=_DEFAULT_SECURE_CHANGE_CA_FILE,
        condition=file_path_exists,
        messages={"condition": "{name} has to be a valid path to a file."},
    ),
)


try:
    # Run validation to populate all settings with defaults if not set.
    SETTINGS.validators.validate_all()
except ValidationError:  # pragma: no cover
    # If any setting is invalid, don't exit just yet — we're still at app
    # initialisation.  Callers decide when all settings must be valid.
    pass
