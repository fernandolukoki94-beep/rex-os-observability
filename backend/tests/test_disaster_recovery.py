from backend.core.services.events import OperationalEvent, SyncStatus
from backend.core.services.offline_engine import OfflineEventEngine


def make_event(event_id: str) -> OperationalEvent:
    return OperationalEvent.create(
        event_id=event_id,
        event_type="EQUIPMENT_INCIDENT",
        description="Chaos test event",
        source_device="edge-chaos-01",
        operator="tester",
        location="Pit North",
    )


def test_corrupt_store_fails_closed_without_crashing(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("{not-json", encoding="utf-8")
    engine = OfflineEventEngine(str(path))
    assert engine.all_events() == []
    event = engine.enqueue(make_event("CHAOS-CORRUPT-001"))
    assert event.sync_status == SyncStatus.PENDING
    assert OfflineEventEngine(str(path)).get("CHAOS-CORRUPT-001") is not None


def test_partial_sync_failure_preserves_success_and_failure_states(tmp_path):
    engine = OfflineEventEngine(str(tmp_path / "events.json"))
    engine.enqueue(make_event("CHAOS-PARTIAL-001"))
    engine.enqueue(make_event("CHAOS-PARTIAL-002"))

    def sender(event):
        return event.event_id.endswith("001")

    results = engine.sync_pending(sender)
    assert [event.sync_status for event in results] == [SyncStatus.SYNCED, SyncStatus.FAILED]
    reloaded = OfflineEventEngine(str(tmp_path / "events.json"))
    assert reloaded.get("CHAOS-PARTIAL-001").sync_status == SyncStatus.SYNCED
    failed = reloaded.get("CHAOS-PARTIAL-002")
    assert failed.sync_status == SyncStatus.FAILED
    assert failed.next_retry_at is not None
    assert failed.retry_delay_seconds is not None
