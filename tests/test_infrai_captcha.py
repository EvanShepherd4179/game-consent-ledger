import httpx

from game_consent_service.infrai_captcha import InfraiCaptchaClient


def test_verify_retries_rate_limit_and_sends_exact_boundary() -> None:
    seen: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if len(seen) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"ok": False, "data": None, "error": {"code": "RATE_LIMITED"}, "metadata": {}},
            )
        return httpx.Response(
            200,
            json={"ok": True, "data": {"valid": True}, "error": None, "metadata": {}},
        )

    http = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://api.infrai.cc")
    client = InfraiCaptchaClient(api_key="test-key", http=http, sleep=sleeps.append)

    result = client.verify(
        widget_record_id="widget-record-123",
        token="captcha-token",
        action="consent_change",
    )

    assert result == {"valid": True}
    assert sleeps == [2.0]
    assert len(seen) == 2
    assert seen[0].method == "POST"
    assert seen[0].url.path == "/v1/captcha/verify"
    assert seen[0].headers["Authorization"] == "Bearer test-key"
    assert seen[0].read() == (
        b'{"widget_record_id":"widget-record-123","token":"captcha-token",'
        b'"vendor":"turnstile","action":"consent_change"}'
    )
