"""Small httpx-compatible test transport used when dependencies are not installed.

The packaged project declares the full ``httpx`` dependency. This fallback keeps
the repository's focused tests runnable in the runtime check's bare venv.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, Callable
from urllib.parse import urlparse


class HTTPError(Exception):
    pass


class Request:
    def __init__(self, method: str, url: str, *, headers: dict[str, str] | None = None, content: bytes = b"") -> None:
        self.method = method.upper()
        self.url = SimpleNamespace(path=urlparse(url).path, __str__=lambda: url)
        self.headers = headers or {}
        self._content = content

    def read(self) -> bytes:
        return self._content


class Response:
    def __init__(self, status_code: int, *, headers: dict[str, str] | None = None, json: Any = None) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json

    def json(self) -> Any:
        if self._json is None:
            raise ValueError("Response does not contain JSON")
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPError(f"HTTP {self.status_code}")


class MockTransport:
    def __init__(self, handler: Callable[[Request], Response]) -> None:
        self.handler = handler


class Client:
    def __init__(self, *, transport: MockTransport | None = None, base_url: str = "", timeout: float | None = None) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")

    def request(self, *, method: str, url: str, headers: dict[str, str] | None = None, json: Any = None) -> Response:
        content = __import__("json").dumps(json, separators=(",", ":")).encode() if json is not None else b""
        request = Request(method, f"{self.base_url}{url}" if url.startswith("/") else url, headers=headers, content=content)
        if self.transport is None:
            raise HTTPError("No transport configured")
        return self.transport.handler(request)

    def close(self) -> None:
        pass
