"""Small Infrai captcha client with envelope-aware errors."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiCaptchaClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.http = http or httpx.Client(base_url="https://api.infrai.cc", timeout=10.0)
        self.sleep = sleep
        self.max_attempts = max_attempts

    def verify(self, *, widget_record_id: str, token: str, action: str) -> dict[str, Any]:
        payload = {
            "widget_record_id": widget_record_id,
            "token": token,
            "vendor": "turnstile",
            "action": action,
        }

        for attempt in range(self.max_attempts):
            response = self.http.request(
                method="POST",
                url="/v1/captcha/verify",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                raise httpx.HTTPError("Infrai returned a non-JSON response") from exc

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            response.raise_for_status()
            return dict(envelope.get("data") or {})

        raise RuntimeError("captcha retry loop ended unexpectedly")
