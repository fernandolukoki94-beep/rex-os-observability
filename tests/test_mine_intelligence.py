from core.services import OfflineEventEngine, OperationalEvent, SyncStatus
from simulator.mine import MineSimulator


def make_event():
    return OperationalEvent.create(
        event_id="REX-EVT-000001",
        event_type="EQUIPMENT_INCIDENT",
        description="Vibração acima do normal",
        source_device="field-device-07",
        operator="operator-demo-01",
        location="Pit North",
        payload={"vibration": 6.2},
        created_at="2026-08-15T10:00:00+00:00",
    )


def test_operational_event_creates_integrity_chain():
    event = make_event()
    assert event.sync_status is SyncStatus.PENDING
    assert len(event.integrity_hash) == 64
    assert [entry.event for entry in event.evidence] == [
        "EVENT_CREATED",
        "LOCAL_STORED",
        "HASH_CREATED",
    ]


def test_offline_engine_persists_and_syncs_idempotently(tmp_path):
    engine = OfflineEventEngine(str(tmp_path / "events.json"))
    event = make_event()
    engine.enqueue(event)
    engine.enqueue(event)
    assert len(engine.all_events()) == 1
    assert len(engine.pending_events()) == 1

    results = engine.sync_pending(lambda item: item.event_id == "REX-EVT-000001")
    assert results[0].sync_status is SyncStatus.SYNCED
    assert [entry.event for entry in results[0].evidence][-4:] == [
        "SYNC_STARTED",
        "SYNCED",
        "SYNC_STARTED",
        "SYNCED",
    ] or [entry.event for entry in results[0].evidence][-2:] == [
        "SYNC_STARTED",
        "SYNCED",
    ]
    reloaded = OfflineEventEngine(str(tmp_path / "events.json"))
    assert reloaded.get("REX-EVT-000001").sync_status is SyncStatus.SYNCED


def test_failed_sync_is_retryable(tmp_path):
    engine = OfflineEventEngine(str(tmp_path / "events.json"))
    engine.enqueue(make_event())
    failed = engine.sync_pending(lambda _: False)
    assert failed[0].sync_status is SyncStatus.FAILED
    assert len(engine.pending_events()) == 1
    recovered = engine.sync_pending(lambda _: True)
    assert recovered[0].sync_status is SyncStatus.SYNCED


def test_mine_simulator_marks_controlled_anomaly():
    simulator = MineSimulator()
    sequence = simulator.pump_vibration_sequence()
    assert sequence[0].vibration == 3.1
    assert sequence[-1].vibration == 6.2
    assert all(not sample.anomaly_detected for sample in sequence[:4])
    assert all(sample.anomaly_detected for sample in sequence[4:])
