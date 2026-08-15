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
