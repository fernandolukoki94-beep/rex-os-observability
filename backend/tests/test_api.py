import json

import pytest

from backend.core.rex_core import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from backend.core import rex_core

    engine = rex_core.OfflineEventEngine(str(tmp_path / "events.json"))
    telemetry = rex_core.JsonTelemetryRepository(str(tmp_path / "telemetry.json"))
    audit = rex_core.JsonAuditLog(str(tmp_path / "audit.json"))
    monkeypatch.setattr(rex_core, "event_engine", engine)
    monkeypatch.setattr(rex_core, "telemetry_repository", telemetry)
    monkeypatch.setattr(rex_core, "audit_log", audit)
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


def test_rbac_and_audit_log_are_available_when_enabled(client, monkeypatch):
    monkeypatch.setenv("REX_RBAC_ENFORCED", "1")
    payload = {
        "event_id": "REX-RBAC-001",
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Evento protegido",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
    }
    denied = client.post("/api/events", json=payload, headers={"X-REX-Role": "VIEWER"})
    assert denied.status_code == 403
    allowed = client.post("/api/events", json=payload, headers={"X-REX-Role": "SUPERVISOR", "X-REX-Actor": "fernando"})
    assert allowed.status_code == 201
    audit = client.get("/api/audit").get_json()["data"]
    assert audit[0]["result"] == "denied"
    assert audit[-1]["actor"] == "fernando"


def test_rex_health_reports_runtime_components(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "rex-observability"
    assert payload["components"]["database"]["adapter"] == "JsonTelemetryRepository"
    assert payload["components"]["edge"]["adapter"] == "SyntheticTelemetryAdapter"
    assert payload["components"]["telemetry"]["source"] == "synthetic"
    assert "max_rss_kb" in payload["process"]


def test_optional_api_key_rejects_missing_and_wrong_keys(client, monkeypatch):
    monkeypatch.setenv("REX_API_KEY", "local-demo-secret")
    missing = client.get("/api/health")
    wrong = client.get("/api/health", headers={"X-REX-API-Key": "wrong"})
    correct = client.get("/api/health", headers={"X-REX-API-Key": "local-demo-secret"})
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert correct.status_code == 200


def test_prometheus_metrics_expose_rex_runtime_signals(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    body = response.get_data(as_text=True)
    assert "# TYPE rex_api_requests_total counter" in body
    assert "rex_queue_depth 0" in body
    assert "rex_queue_age_seconds 0.0" in body
    assert "rex_dead_letter_events_total 0" in body


def test_health_reports_queue_age_for_pending_event(client):
    payload = {
        "event_id": "REX-QUEUE-AGE-001",
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Evento pendente para teste de idade",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
        "created_at": "2020-01-01T00:00:00+00:00",
    }
    assert client.post("/api/events", json=payload).status_code == 201
    health = client.get("/api/health").get_json()
    assert health["components"]["queue"]["depth"] == 1
    assert health["components"]["queue"]["age_seconds"] > 0
    metrics = client.get("/metrics").get_data(as_text=True)
    assert "rex_queue_depth 1" in metrics
    assert "rex_queue_age_seconds " in metrics



def test_dead_letter_replay_requires_supervised_role_and_requeues(client, monkeypatch):
    monkeypatch.setenv("REX_RBAC_ENFORCED", "1")
    payload = {
        "event_id": "REX-REPLAY-001",
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Evento para replay supervisionado",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
    }
    headers = {"X-REX-Role": "SUPERVISOR", "X-REX-Actor": "fernando"}
    assert client.post("/api/events", json=payload, headers=headers).status_code == 201
    from backend.core import rex_core
    event = rex_core.event_engine.get("REX-REPLAY-001")
    assert event is not None
    event.retry_count = 3
    event.dead_letter = True
    event.sync_status = rex_core.OperationalEvent.from_dict(event.to_dict()).sync_status
    rex_core.event_engine.replace([event])
    denied = client.post("/api/events/dead-letter/replay", json={"event_id": "REX-REPLAY-001"}, headers={"X-REX-Role": "VIEWER"})
    assert denied.status_code == 403
    replayed = client.post("/api/events/dead-letter/replay", json={"event_id": "REX-REPLAY-001"}, headers=headers)
    assert replayed.status_code == 200
    assert replayed.get_json()["data"]["sync_status"] == "PENDING"
    assert replayed.get_json()["data"]["dead_letter"] is False
    assert replayed.get_json()["data"]["evidence"][-1]["event"] == "DEAD_LETTER_REPLAYED"


def test_same_event_id_with_different_payload_is_conflict(client):
    payload = {
        "event_id": "REX-CONFLICT-001",
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Primeiro conteúdo",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
        "payload": {"vibration": 4.2},
    }
    assert client.post("/api/events", json=payload).status_code == 201
    conflict = client.post("/api/events", json={**payload, "description": "Conteúdo adulterado"})
    assert conflict.status_code == 409
    body = conflict.get_json()
    assert body["status"] == "conflict"
    assert body["existing_hash"] != body["incoming_hash"]
    assert client.get("/api/events").get_json()["data"][0]["description"] == "Primeiro conteúdo"


def test_events_expose_chained_hashes(client):
    base = {
        "event_type": "EQUIPMENT_INCIDENT",
        "description": "Evento encadeado",
        "source_device": "field-device-07",
        "operator": "operator-demo-01",
        "location": "Pit North",
    }
    first = client.post("/api/events", json={**base, "event_id": "REX-CHAIN-001"}).get_json()["data"]
    second = client.post("/api/events", json={**base, "event_id": "REX-CHAIN-002"}).get_json()["data"]
    assert first["chain_hash"]
    assert second["previous_event_hash"] == first["chain_hash"]
    assert second["chain_hash"] != first["chain_hash"]
