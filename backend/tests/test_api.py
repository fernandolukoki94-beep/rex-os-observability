import json

import pytest

from backend.core.rex_core import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from backend.core import rex_core

    engine = rex_core.OfflineEventEngine(str(tmp_path / "events.json"))
    telemetry = rex_core.JsonTelemetryRepository(str(tmp_path / "telemetry.json"))
    monkeypatch.setattr(rex_core, "event_engine", engine)
    monkeypatch.setattr(rex_core, "telemetry_repository", telemetry)
    app.config.update({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


def test_dashboard_is_served_by_rex_core(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'REX-OS' in response.data
    assert b'Mine Intelligence' in response.data


def test_create_list_and_sync_event(client):
    payload = {
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Vibração elevada no arranque",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
        "payload": {"equipment_id": "PUMP-017", "vibration": 6.2},
    }
    response = client.post("/api/events", data=json.dumps(payload), content_type="application/json")
    assert response.status_code == 201
    event = response.get_json()["data"]
    assert event["sync_status"] == "PENDING"
    assert event["evidence"][-1]["event"] == "SYNC_PENDING"

    listed = client.get("/api/events")
    assert listed.status_code == 200
    assert len(listed.get_json()["data"]) == 1

    synced = client.post("/api/events/sync")
    assert synced.status_code == 200
    assert len(synced.get_json()["synced"]) == 1
    assert synced.get_json()["synced"][0]["sync_status"] == "SYNCED"


def test_duplicate_event_id_is_idempotent(client):
    payload = {
        "event_id": "REX-IDEMPOTENCY-001",
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Evento repetido de teste",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
        "payload": {"equipment_id": "PUMP-017"},
    }
    first = client.post("/api/events", json=payload)
    second = client.post("/api/events", json=payload)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.get_json()["idempotent"] is True
    assert len(client.get("/api/events").get_json()["data"]) == 1


def test_telemetry_history_persists_and_reports_latest(client, tmp_path):
    update = client.post("/api/monitor/v1/update", json={"server_name": "edge-01", "cpu": 91, "ram": 44})
    assert update.status_code == 200
    status = client.get("/api/monitor/v1/status")
    assert status.get_json()["edge-01"]["cpu"] == 91
    assert (tmp_path / "telemetry.json").exists()


def test_event_validation_and_mine_telemetry(client):
    invalid = client.post("/api/events", json={"description": "missing fields"})
    assert invalid.status_code == 400
    assert set(invalid.get_json()["fields"]) == {
        "event_type",
        "source_device",
        "operator",
        "location",
    }

    telemetry = client.get("/api/telemetry/mine")
    assert telemetry.status_code == 200
    assert {sample["equipment_id"] for sample in telemetry.get_json()["data"]} == {
        "PUMP-017",
        "TRUCK-021",
        "CONVEYOR-04",
        "GENERATOR-02",
    }

    sequence = client.get("/api/telemetry/mine/pump-sequence")
    assert sequence.get_json()["message"] == "Anomaly detected"
    assert sequence.get_json()["data"][-1]["anomaly_detected"] is True
