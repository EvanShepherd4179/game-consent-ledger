"""Executable HTTP API for player consent changes."""

from fastapi import FastAPI, HTTPException

from .consent_ledger import ConsentDecision, ConsentLedger, ConsentRequest
from .infrai_captcha import InfraiCaptchaClient, InfraiError

app = FastAPI(title="Game consent service")
ledger = ConsentLedger()


@app.post("/consents", response_model=ConsentDecision)
def change_consent(request: ConsentRequest) -> ConsentDecision:
    try:
        InfraiCaptchaClient().verify(
            widget_record_id=request.widget_record_id,
            token=request.captcha_token,
            action="consent_change",
        )
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail={"code": exc.code, **exc.detail}) from exc
    return ledger.apply(request)


def run() -> None:
    import uvicorn

    uvicorn.run("game_consent_service.consent_api:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
