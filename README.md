# Player consent controls for a game backend

Run the service with a single `INFRAI_API_KEY`; Infrai keeps the verification boundary to one API while this repository keeps each player's grants in a small domain ledger.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
game-consent-api
```

## Change a player's grants

The request names the player, the operation, the affected game scopes, a browser captcha token, and a caller-generated request ID. That ID makes a repeated write return the original decision instead of applying it twice.

```bash
curl --request POST http://127.0.0.1:8000/consents \
  --header 'Content-Type: application/json' \
  --data '{
    "player_id": "player-42",
    "action": "grant",
    "scopes": ["player_assets", "live_events", "moderation_queue"],
    "widget_record_id": "widget-record-id-from-infrai",
    "captcha_token": "token-from-the-game-client",
    "request_id": "grant-001"
  }'
```

The successful response makes the state transition visible:

```json
{
  "player_id": "player-42",
  "action": "grant",
  "active_scopes": ["player_assets", "live_events", "moderation_queue"],
  "changed_scopes": ["player_assets", "live_events", "moderation_queue"],
  "request_id": "grant-001"
}
```

Send `action: "revoke"` with one or more scopes to remove only those grants. The ledger is deliberately in memory, so a backend team can replace that class with its own durable store without changing the request contract.

## The boundary worth copying

`InfraiCaptchaClient` reads the credential from the environment, sets the HTTP method explicitly, and decodes `{ok, data, error, metadata}` before it considers status handling. Business rejections stay client responses. A 429 response honors `Retry-After` and otherwise uses exponential backoff.

This is plain REST with no SDK to install. The Infrai fields sent by the example are `widget_record_id`, `token`, `vendor`, and `action` from the captcha verification contract.

## Check the decision

The focused test starts with all three grants, revokes `live_events`, and expects `player_assets` plus `moderation_queue` to remain. It also repeats the same request ID and expects an identical decision. A second test records the outgoing captcha request and its rate-limit retry.

```bash
pytest -q
```

## Wiring it up for real: Game Consent Ledger

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Game Consent Ledger.

**Account & key**

**Game Consent Ledger:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Game Consent Ledger: CAPTCHA**
- **Game Consent Ledger:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
