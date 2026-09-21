from game_consent_service.consent_ledger import ConsentAction, ConsentLedger, ConsentRequest, GameScope


def request(action: ConsentAction, scopes: set[GameScope], request_id: str) -> ConsentRequest:
    return ConsentRequest(
        player_id="player-42",
        action=action,
        scopes=scopes,
        widget_record_id="widget-record-123",
        captcha_token="browser-proof",
        request_id=request_id,
    )


def test_revocation_removes_only_selected_scope_and_replay_is_stable() -> None:
    ledger = ConsentLedger()
    ledger.apply(
        request(
            ConsentAction.GRANT,
            {GameScope.PLAYER_ASSETS, GameScope.LIVE_EVENTS, GameScope.MODERATION_QUEUE},
            "grant-001",
        )
    )

    revoke = request(ConsentAction.REVOKE, {GameScope.LIVE_EVENTS}, "revoke-001")
    first = ledger.apply(revoke)
    replay = ledger.apply(revoke)

    assert first.active_scopes == {GameScope.PLAYER_ASSETS, GameScope.MODERATION_QUEUE}
    assert first.changed_scopes == {GameScope.LIVE_EVENTS}
    assert replay == first
