from backend.core.services.events import OperationalEvent, SyncStatus
from backend.core.services.offline_engine import OfflineEventEngine


def make_event():
    return OperationalEvent.create(
        event_id="RETRY-001",
        event_type="EQUIPMENT_INCIDENT",
        description="Transport failure test",
        source_device="edge-01",
        operator="tester",
        location="Pit North",
    )


def test_failed_events_get_retry_metadata_and_dead_letter(tmp_path):
    engine = OfflineEventEngine(str(tmp_path / "events.json"))
    engine.enqueue(make_event())
    for _ in range(3):
        result = engine.sync_pending(lambda event: False)
        assert result[0].sync_status == SyncStatus.FAILED
    event = engine.get("RETRY-001")
    assert event is not None
    assert event.retry_count == 3
    assert event.dead_letter is True
    assert event.failure_reason
    assert any(entry.event == "DEAD_LETTER" for entry in event.evidence)


def test_retry_metadata_survives_reload(tmp_path):
    path = tmp_path / "events.json"
    engine = OfflineEventEngine(str(path))
    engine.enqueue(make_event())
    engine.sync_pending(lambda event: False)
    reloaded = OfflineEventEngine(str(path))
    event = reloaded.get("RETRY-001")
    assert event is not None
    assert event.retry_count == 1
    assert event.last_attempt is not None
    assert event.next_retry_at is not None


def test_retry_jitter_is_recorded_and_persists(tmp_path, monkeypatch):
    path = tmp_path / "events.json"
    engine = OfflineEventEngine(str(path))
    engine.enqueue(make_event())
    monkeypatch.setattr("backend.core.services.events.random.uniform", lambda low, high: high)
    engine.sync_pending(lambda event: False)
    event = engine.get("RETRY-001")
    assert event is not None
    assert event.retry_delay_seconds == 1.25
    assert any(entry.event == "RETRY_SCHEDULED" for entry in event.evidence)
    reloaded = OfflineEventEngine(str(path)).get("RETRY-001")
    assert reloaded is not None
    assert reloaded.retry_delay_seconds == 1.25


def test_dead_letter_replay_requeues_event(tmp_path):
    engine = OfflineEventEngine(str(tmp_path / "events.json"))
    engine.enqueue(make_event())
    for _ in range(3):
        engine.sync_pending(lambda event: False)
    replayed = engine.replay_dead_letter("RETRY-001")
    assert replayed.dead_letter is False
    assert replayed.sync_status == SyncStatus.PENDING
    assert replayed.retry_count == 0
    assert any(entry.event == "DEAD_LETTER_REPLAYED" for entry in replayed.evidence)
