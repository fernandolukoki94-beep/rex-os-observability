from flask import Flask, Response, g, jsonify, render_template, request
import hmac
import os
import resource
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.core.services import (
    JsonTelemetryRepository,
    EventConflictError,
    OfflineEventEngine,
    OperationalEvent,
)
from backend.core.services.access_control import actor_from_headers
from backend.core.services.audit_log import JsonAuditLog
from backend.simulator.mine.telemetry import MineSimulator

app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent.parent.parent / "templates"))


@app.before_request
def enforce_optional_api_key():
    """Require X-REX-API-Key only when configured by the deployment."""
    configured_key = os.getenv("REX_API_KEY")
    if configured_key and request.path.startswith("/api"):
        supplied_key = request.headers.get("X-REX-API-Key", "")
        if not hmac.compare_digest(supplied_key, configured_key):
            return jsonify({"status": "error", "message": "API key required"}), 401
    return None

_runtime_store_dir = "/tmp/rex-data" if os.getenv("VERCEL") else "data"
telemetry_repository = JsonTelemetryRepository(
    os.getenv("REX_TELEMETRY_STORE", f"{_runtime_store_dir}/telemetry_history.json")
)
event_engine = OfflineEventEngine(
    os.getenv("REX_EVENT_STORE", f"{_runtime_store_dir}/offline_events.json")
)
mine_simulator = MineSimulator()
audit_log = JsonAuditLog(os.getenv("REX_AUDIT_STORE", f"{_runtime_store_dir}/audit_log.json"))
_request_latencies_ms = []
_api_request_count = 0
_api_error_count = 0
_sync_success_count = 0
_sync_failure_count = 0


@app.before_request
def start_request_timer():
    g.rex_started_at = time.perf_counter()
    supplied_trace_id = request.headers.get("X-REX-Trace-ID", "").strip()
    g.rex_trace_id = supplied_trace_id[:128] if supplied_trace_id else uuid.uuid4().hex


@app.after_request
def record_request_metrics(response):
    global _api_request_count, _api_error_count
    response.headers["X-REX-Trace-ID"] = getattr(g, "rex_trace_id", uuid.uuid4().hex)
    if request.path.startswith("/api"):
        _api_request_count += 1
        elapsed_ms = (time.perf_counter() - getattr(g, "rex_started_at", time.perf_counter())) * 1000
        _request_latencies_ms.append(round(elapsed_ms, 2))
        del _request_latencies_ms[:-100]
        if response.status_code >= 400:
            _api_error_count += 1
    return response


@app.route('/', methods=['GET'])
def dashboard():
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def rex_health():
    """Expose operational health of the REX runtime itself."""
    events = event_engine.all_events()
    failed = sum(1 for event in events if event.sync_status.value == "FAILED")
    pending = sum(1 for event in events if event.sync_status.value in {"PENDING", "SYNCING"})
    queue_age_seconds = 0.0
    pending_events = [event for event in events if event.sync_status.value in {"PENDING", "SYNCING", "FAILED"}]
    if pending_events:
        try:
            oldest = min(datetime.fromisoformat(event.created_at.replace("Z", "+00:00")) for event in pending_events)
            queue_age_seconds = max(0.0, round((datetime.now(timezone.utc) - oldest).total_seconds(), 2))
        except (TypeError, ValueError):
            queue_age_seconds = 0.0
    store_path = Path(os.getenv("REX_TELEMETRY_STORE", "data/telemetry_history.json"))
    storage_bytes = store_path.stat().st_size if store_path.exists() else 0
    avg_latency = round(sum(_request_latencies_ms) / len(_request_latencies_ms), 2) if _request_latencies_ms else 0
    return jsonify({
        "status": "healthy",
        "service": "rex-observability",
        "components": {
            "api": {"status": "healthy", "latency_ms_avg": avg_latency, "errors": _api_error_count},
            "database": {"status": "healthy", "adapter": "JsonTelemetryRepository"},
            "queue": {"status": "healthy" if failed == 0 else "degraded", "depth": pending, "failed": failed, "age_seconds": queue_age_seconds},
            "edge": {"status": "healthy", "adapter": "SyntheticTelemetryAdapter"},
            "sync": {"status": "healthy" if failed == 0 else "degraded", "pending": pending, "failed": failed},
            "storage": {"status": "healthy", "events": len(events), "telemetry_bytes": storage_bytes},
            "telemetry": {"status": "healthy", "source": "synthetic"},
        },
        "process": {"max_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        "trace_id": getattr(g, "rex_trace_id", None),
    }), 200


# Configuração de Alertas (Podes trocar pelo Webhook real do teu bot do Telegram/WhatsApp)
def send_infrastructure_alert(server_name, metric, value):
    print(f"\n🚨 [ALERTA DE SISTEMA] Servidor '{server_name}' está instável!")
    print(f"⚠️ {metric} atingiu {value}%! Verificando logs de segurança...")
    # Aqui futuramente inserimos o requests.post() para a API do Telegram

@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Expose a dependency-free Prometheus text surface for the REX runtime."""
    events = event_engine.all_events()
    pending_events = [event for event in events if event.sync_status.value in {"PENDING", "SYNCING", "FAILED"}]
    queue_age_seconds = 0.0
    if pending_events:
        try:
            oldest = min(datetime.fromisoformat(event.created_at.replace("Z", "+00:00")) for event in pending_events)
            queue_age_seconds = max(0.0, round((datetime.now(timezone.utc) - oldest).total_seconds(), 2))
        except (TypeError, ValueError):
            queue_age_seconds = 0.0
    lines = [
        "# HELP rex_api_requests_total Total API requests observed by the REX process; process-scoped and reset on restart.",
        "# TYPE rex_api_requests_total counter",
        f"rex_api_requests_total {_api_request_count}",
        "# HELP rex_api_errors_total Total API responses with status >= 400.",
        "# TYPE rex_api_errors_total counter",
        f"rex_api_errors_total {_api_error_count}",
        "# HELP rex_queue_depth Current number of pending or syncing events.",
        "# TYPE rex_queue_depth gauge",
        f"rex_queue_depth {len([event for event in events if event.sync_status.value in {'PENDING', 'SYNCING'}])}",
        "# HELP rex_queue_age_seconds Age in seconds of the oldest pending, syncing or failed event.",
        "# TYPE rex_queue_age_seconds gauge",
        f"rex_queue_age_seconds {queue_age_seconds}",
        "# HELP rex_events_total Total operational events persisted by the REX process.",
        "# TYPE rex_events_total gauge",
        f"rex_events_total {len(events)}",
        "# HELP rex_sync_success_total Total events synchronised successfully.",
        "# TYPE rex_sync_success_total counter",
        f"rex_sync_success_total {_sync_success_count}",
        "# HELP rex_sync_failures_total Total failed synchronisation attempts.",
        "# TYPE rex_sync_failures_total counter",
        f"rex_sync_failures_total {_sync_failure_count}",
        "# HELP rex_trace_requests_total Requests assigned a REX trace identifier; process-scoped.",
        "# TYPE rex_trace_requests_total counter",
        f"rex_trace_requests_total {_api_request_count}",
        "# HELP rex_dead_letter_events_total Total events in dead-letter state.",
        "# TYPE rex_dead_letter_events_total gauge",
        f"rex_dead_letter_events_total {len([event for event in events if event.dead_letter])}",
    ]
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route('/api/monitor/v1/update', methods=['POST'])
def receive_metrics():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
        
    server_name = data.get("server_name", "Unknown_Node")
    cpu = data.get("cpu", 0)
    ram = data.get("ram", 0)
    
    # Persiste o histórico do nó através de uma boundary substituível.
    telemetry_repository.append(
        server_name,
        {"timestamp": time.time(), "cpu": cpu, "ram": ram},
    )
    
    # Lógica de Deteção de Anomalias (Regra básica de Limiar)
    if cpu > 85:
        send_infrastructure_alert(server_name, "Uso de CPU", cpu)
    if ram > 90:
        send_infrastructure_alert(server_name, "Uso de Memória RAM", ram)
        
    return jsonify({"status": "success", "node": server_name, "received": True}), 200

@app.route('/api/events', methods=['POST'])
def create_operational_event():
    actor = actor_from_headers(request.headers.get("X-REX-Actor"), request.headers.get("X-REX-Role") or ("OPERATOR" if not os.getenv("REX_RBAC_ENFORCED") else None))
    if os.getenv("REX_RBAC_ENFORCED") and not actor.can("write"):
        audit_log.record(actor=actor.actor_id, role=actor.role, action="create_event", resource="operational_event", result="denied")
        return jsonify({"status": "error", "message": "role lacks write permission"}), 403
    data = request.get_json(silent=True) or {}
    required = ["event_type", "description", "source_device", "operator", "location"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"status": "error", "message": "Missing fields", "fields": missing}), 400

    event_id = data.get("event_id") or f"REX-EVT-{uuid.uuid4().hex[:12].upper()}"
    existing = event_engine.get(event_id)
    event = OperationalEvent.create(
        event_id=event_id,
        event_type=data["event_type"],
        description=data["description"],
        source_device=data["source_device"],
        operator=data["operator"],
        location=data["location"],
        payload=data.get("payload", {}),
        created_at=data.get("created_at") or (existing.created_at if existing else None),
    )
    try:
        stored_event = event_engine.enqueue(event)
    except EventConflictError:
        audit_log.record(
            actor=actor.actor_id,
            role=actor.role,
            action="create_event",
            resource=event_id,
            result="conflict",
            metadata={"existing_hash": existing.integrity_hash if existing else None, "incoming_hash": event.integrity_hash},
        )
        return jsonify({
            "status": "conflict",
            "message": "event_id already exists with a different integrity hash",
            "event_id": event_id,
            "existing_hash": existing.integrity_hash if existing else None,
            "incoming_hash": event.integrity_hash,
        }), 409
    if existing is not None:
        audit_log.record(actor=actor.actor_id, role=actor.role, action="create_event", resource=event_id, result="idempotent")
        return jsonify({"status": "success", "idempotent": True, "data": stored_event.to_dict()}), 200
    audit_log.record(actor=actor.actor_id, role=actor.role, action="create_event", resource=event_id, result="created")
    return jsonify({"status": "success", "data": stored_event.to_dict()}), 201


@app.route('/api/events', methods=['GET'])
def list_operational_events():
    return jsonify({"status": "success", "data": [event.to_dict() for event in event_engine.all_events()]}), 200


@app.route('/api/events/dead-letter/replay', methods=['POST'])
def replay_dead_letter_event():
    actor = actor_from_headers(request.headers.get("X-REX-Actor"), request.headers.get("X-REX-Role") or ("OPERATOR" if not os.getenv("REX_RBAC_ENFORCED") else None))
    if os.getenv("REX_RBAC_ENFORCED") and not actor.can("sync"):
        audit_log.record(actor=actor.actor_id, role=actor.role, action="replay_dead_letter", resource="offline_queue", result="denied")
        return jsonify({"status": "error", "message": "role lacks replay permission"}), 403
    event_id = (request.get_json(silent=True) or {}).get("event_id")
    if not event_id:
        return jsonify({"status": "error", "message": "event_id is required"}), 400
    try:
        event = event_engine.replay_dead_letter(event_id)
    except KeyError:
        return jsonify({"status": "error", "message": "event not found"}), 404
    except ValueError:
        return jsonify({"status": "error", "message": "event is not dead-lettered"}), 409
    audit_log.record(actor=actor.actor_id, role=actor.role, action="replay_dead_letter", resource=event_id, result="requeued")
    return jsonify({"status": "success", "data": event.to_dict()}), 200


@app.route('/api/events/sync', methods=['POST'])
def sync_operational_events():
    global _sync_success_count, _sync_failure_count
    actor = actor_from_headers(request.headers.get("X-REX-Actor"), request.headers.get("X-REX-Role") or ("OPERATOR" if not os.getenv("REX_RBAC_ENFORCED") else None))
    if os.getenv("REX_RBAC_ENFORCED") and not actor.can("sync"):
        audit_log.record(actor=actor.actor_id, role=actor.role, action="sync_events", resource="offline_queue", result="denied")
        return jsonify({"status": "error", "message": "role lacks sync permission"}), 403
    synced = event_engine.sync_pending(lambda event: bool(event.event_id and event.description))
    _sync_success_count += sum(1 for event in synced if event.sync_status.value == "SYNCED")
    _sync_failure_count += sum(1 for event in synced if event.sync_status.value == "FAILED")
    audit_log.record(actor=actor.actor_id, role=actor.role, action="sync_events", resource="offline_queue", result="completed", metadata={"count": len(synced)})
    return jsonify({
        "status": "success",
        "synced": [event.to_dict() for event in synced if event.sync_status.value == "SYNCED"],
        "failed": [event.to_dict() for event in synced if event.sync_status.value == "FAILED"],
    }), 200


@app.route('/api/audit', methods=['GET'])
def list_audit_entries():
    return jsonify({"status": "success", "data": audit_log.all()}), 200


@app.route('/api/telemetry/mine', methods=['GET'])
def get_mine_telemetry():
    return jsonify({"status": "success", "data": [sample.to_dict() for sample in mine_simulator.samples()]}), 200


@app.route('/api/telemetry/mine/pump-sequence', methods=['GET'])
def get_pump_sequence():
    sequence = [sample.to_dict() for sample in mine_simulator.pump_vibration_sequence()]
    return jsonify({"status": "success", "data": sequence, "message": "Anomaly detected"}), 200


@app.route('/api/monitor/v1/status', methods=['GET'])
def get_status():
    """Rota que o teu Dashboard TUI vai consumir para pintar a tela"""
    return jsonify(telemetry_repository.latest_by_server())

if __name__ == '__main__':
    # Roda o servidor na porta local 5000 do Termux
    app.run(host='0.0.0.0', port=5000, debug=True)

