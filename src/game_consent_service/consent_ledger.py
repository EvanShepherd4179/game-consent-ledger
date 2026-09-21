"""Domain models and in-memory consent ledger."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class GameScope(StrEnum):
    PLAYER_ASSETS = "player_assets"
    LIVE_EVENTS = "live_events"
    MODERATION_QUEUE = "moderation_queue"


class ConsentAction(StrEnum):
    GRANT = "grant"
    REVOKE = "revoke"


class ConsentRequest(BaseModel):
    player_id: str = Field(min_length=1)
    action: ConsentAction
    scopes: set[GameScope] = Field(min_length=1)
    widget_record_id: str = Field(min_length=1)
    captcha_token: str = Field(min_length=1)
    request_id: str = Field(min_length=1)


class ConsentDecision(BaseModel):
    player_id: str
    action: ConsentAction
    active_scopes: set[GameScope]
    changed_scopes: set[GameScope]
    request_id: str


class ConsentLedger:
    def __init__(self) -> None:
        self._grants: dict[str, set[GameScope]] = {}
        self._decisions: dict[str, ConsentDecision] = {}

    def apply(self, request: ConsentRequest) -> ConsentDecision:
        previous = self._decisions.get(request.request_id)
        if previous is not None:
            return previous

        active = self._grants.setdefault(request.player_id, set())
        before = active.copy()
        if request.action is ConsentAction.GRANT:
            active.update(request.scopes)
        else:
            active.difference_update(request.scopes)

        decision = ConsentDecision(
            player_id=request.player_id,
            action=request.action,
            active_scopes=active.copy(),
            changed_scopes=before.symmetric_difference(active),
            request_id=request.request_id,
        )
        self._decisions[request.request_id] = decision
        return decision
