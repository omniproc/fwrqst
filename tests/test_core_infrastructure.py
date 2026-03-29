# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


# __IMPORTS____________________________________________________________________________________________________________
import re
import ssl

import pytest
from httpx import BasicAuth
from hypothesis import HealthCheck, given
from hypothesis import provisional as pv
from hypothesis import settings as hsettings
from hypothesis import strategies as st

from fwrqst.api.client import ApiClient, Proxy
from fwrqst.api.securechange import SecureChangeClient
from fwrqst.settings import (
    KEY_SECURE_CHANGE_API_BASE_PATH,
    KEY_SECURE_CHANGE_DOMAIN,
    KEY_SECURE_CHANGE_PORT,
    file_path_exists,
)


# __HELPERS____________________________________________________________________________________________________________
def _make_sslctx():
    """Create a permissive SSL context suitable for unit tests (no real connections)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _make_auth():
    """Create a dummy BasicAuth credential for unit tests."""
    return BasicAuth(username="user", password="pass")  # nosec B106


# __PROGRAM____________________________________________________________________________________________________________
class TestApiClient:
    def test_default_port_used_when_port_is_zero(self):
        """When port=0 (falsy), should fall back to ApiClient._PORT (443)."""
        client = ApiClient(auth=_make_auth(), domain="example.com", sslctx=_make_sslctx(), port=0)
        assert client.port == ApiClient._PORT

    def test_explicit_port(self):
        """When port is provided, it should be used."""
        client = ApiClient(auth=_make_auth(), domain="example.com", sslctx=_make_sslctx(), port=8443)
        assert client.port == 8443

    def test_proxy_configuration(self):
        """When proxy settings are provided, client should initialize with proxy mounts."""
        proxy = Proxy(http="http://proxy:8080", https="http://proxy:8443")
        client = ApiClient(auth=_make_auth(), domain="example.com", sslctx=_make_sslctx(), proxy=proxy)
        assert client.port == 443
        assert client.domain == "example.com"

    def test_url_construction(self):
        """URL should be constructed from domain, port, and base path."""
        client = ApiClient(auth=_make_auth(), domain="api.example.com", sslctx=_make_sslctx(), base="/api/v1/", port=8443)
        assert client.url == "https://api.example.com:8443/api/v1"

    def test_base_path_normalization(self):
        """Base path should be normalized to /path format."""
        client = ApiClient(auth=_make_auth(), domain="example.com", sslctx=_make_sslctx(), base="/foo/bar/")
        assert client.base == "/foo/bar"

        client.base = "no/leading/slash/"
        assert client.base == "/no/leading/slash"

    @hsettings(suppress_health_check=[HealthCheck.too_slow])
    @given(
        domain=pv.domains(max_length=255, max_element_length=63),
        port=st.integers(min_value=1, max_value=65535),
        base=st.text(alphabet=st.characters(categories=("L", "N"), whitelist_characters="/"), min_size=1, max_size=30),
    )
    def test_url_matches_pattern(self, domain, port, base):
        """URL should always match https://{domain}:{port}/{base} pattern."""
        client = ApiClient(auth=_make_auth(), domain=domain, sslctx=_make_sslctx(), base=base, port=port)
        assert re.match(r"^https://[^:]+:\d+/\S*$", client.url)


class TestSecureChangeClient:
    def test_raises_on_missing_domain(self):
        """Should raise ValueError when no domain is provided and no setting configured."""
        from fwrqst import settings

        original = settings.SETTINGS.get(KEY_SECURE_CHANGE_DOMAIN, None)
        settings.SETTINGS.set(KEY_SECURE_CHANGE_DOMAIN, "")
        try:
            with pytest.raises(ValueError, match="No domain provided"):
                SecureChangeClient(auth=_make_auth(), sslctx=_make_sslctx(), domain="", port=443, base="/api/")
        finally:
            settings.SETTINGS.set(KEY_SECURE_CHANGE_DOMAIN, original)

    def test_raises_on_missing_port(self, monkeypatch):
        """Should raise ValueError when no port is provided and no setting configured."""
        from fwrqst import settings

        original = settings.SETTINGS.get(KEY_SECURE_CHANGE_PORT, None)
        settings.SETTINGS.set(KEY_SECURE_CHANGE_PORT, 0)
        try:
            with pytest.raises(ValueError, match="No port provided"):
                SecureChangeClient(auth=_make_auth(), sslctx=_make_sslctx(), domain="example.com", port=0, base="/api/")
        finally:
            settings.SETTINGS.set(KEY_SECURE_CHANGE_PORT, original)

    def test_raises_on_missing_base(self, monkeypatch):
        """Should raise ValueError when no base path is provided and no setting configured."""
        from fwrqst import settings

        original = settings.SETTINGS.get(KEY_SECURE_CHANGE_API_BASE_PATH, None)
        settings.SETTINGS.set(KEY_SECURE_CHANGE_API_BASE_PATH, "")
        try:
            with pytest.raises(ValueError, match="No api base path provided"):
                SecureChangeClient(auth=_make_auth(), sslctx=_make_sslctx(), domain="example.com", port=443, base="")
        finally:
            settings.SETTINGS.set(KEY_SECURE_CHANGE_API_BASE_PATH, original)


class TestFilePathExists:
    def test_none_returns_true(self):
        assert file_path_exists(None) is True

    def test_empty_string_returns_true(self):
        assert file_path_exists("") is True

    def test_existing_file_returns_true(self, tmp_path):
        f = tmp_path / "test.pem"
        f.write_text("cert")
        assert file_path_exists(str(f)) is True

    def test_nonexistent_file_returns_false(self):
        assert file_path_exists("/nonexistent/path/to/file.pem") is False

    def test_invalid_path_returns_false(self, mocker):
        """Path that raises an exception inside is_file() should return False."""
        mocker.patch("fwrqst.settings.Path.is_file", side_effect=OSError("bad path"))
        assert file_path_exists("/some/path.pem") is False
