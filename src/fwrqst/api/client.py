# -*- coding: utf-8 -*-
# Copyright (c) 2024 Robert Ruf
# SPDX-License-Identifier: MIT


"""
Generic HTTPS API client built on ``httpx.Client``.

Provides a reusable base class that handles URL construction, TLS
verification, optional proxy support, and HTTP basic authentication.
"""

# __IMPORTS______________________________________________________________________________________________________________
from dataclasses import dataclass
from ssl import SSLContext

from httpx import BasicAuth, Client, HTTPTransport


# __PROGRAM______________________________________________________________________________________________________________
@dataclass
class Proxy:
    """
    Proxy settings.

    Args:
        http (str): URL to use when connecting via HTTP
        https (str): URL to use when connecting via HTTPS

    Returns:
        Proxy: A proxy settings object
    """

    http: str | None = None
    https: str | None = None


class ApiClient(Client):
    """
    API client.

    Args:
        domain (str): The URL domain of the API
        sslctx (SSLContext): SSL context to use
        auth (BasicAuth): HTTP basic authentication object
        base (str): Base path of the API
        port (int): Port number
        proxy (Proxy): Proxy settings

    Returns:
        ApiClient: An API client
    """

    # Disable the use of any system proxy.
    # Proxies must be set explicitly via the proxy parameter.
    _PROXY = Proxy()

    # Default HTTPS port used when none is provided.
    _PORT = 443

    # Default base path (root) when none is provided.
    _DEFAULT_BASE_PATH = "/"

    def __init__(
        self,
        auth: BasicAuth,
        domain: str,
        sslctx: SSLContext,
        base: str = _DEFAULT_BASE_PATH,
        port: int = _PORT,
        proxy: Proxy = _PROXY,
    ):
        self.domain = domain
        self._sslctx = sslctx
        self.base = base
        self._auth = auth
        self._proxy = proxy

        if port:
            self.port = port
        else:
            self.port = ApiClient._PORT

        if proxy.http or proxy.https:
            # Convert Proxy dataclass to httpx transport mounts.
            _HTTP_SCHEME = "http://"
            _HTTPS_SCHEME = "https://"
            mounts = {
                _HTTP_SCHEME: HTTPTransport(proxy=proxy.http),
                _HTTPS_SCHEME: HTTPTransport(proxy=proxy.https),
            }
            super().__init__(mounts=mounts, verify=sslctx, auth=auth)
        else:
            super().__init__(verify=sslctx, auth=auth)

    @property
    def domain(self) -> str:
        """Hostname of the remote API server."""
        return self._domain

    @domain.setter
    def domain(self, value: str):
        self._domain = value

    @property
    def port(self) -> int:
        """TCP port of the remote API server."""
        return self._port

    @port.setter
    def port(self, value: int):
        self._port = value

    @property
    def base(self) -> str:
        """Normalised base path (always starts with ``/``, no trailing ``/``)."""
        return self._base

    @base.setter
    def base(self, value: str):
        """Normalise *value* into ``/<path>`` form (strip leading/trailing slashes)."""
        value = value.removeprefix("/")
        value = value.removesuffix("/")
        self._base = f"/{value}"

    @property
    def url(self) -> str:
        """Fully-qualified API base URL (``https://domain:port/base``), no trailing slash."""
        return f"https://{self.domain}:{str(self.port)}{self.base}"

    @url.setter
    def url(self, value: str):
        """No-op: the URL is computed dynamically from domain, port, and base."""
        pass  # pragma: no cover
