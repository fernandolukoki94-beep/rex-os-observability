from flask import Flask, request, jsonify
import os
import time
import uuid

from core.services import OfflineEventEngine, OperationalEvent
from simulator.mine.telemetry import MineSimulator

app = Flask(__name__)

# Banco de dados em memória temporário para o histórico de métricas
server_history = {}
event_engine = OfflineEventEngine(os.getenv("REX_EVENT_STORE", "data/offline_events.json"))
mine_simulator = MineSimulator()

# Configuração de Alertas (Podes trocar pelo Webhook real do teu bot do Telegram/WhatsApp)
def send_infrastructure_alert(server_name, metric, value):
    print(f"\n🚨 [ALERTA DE SISTEMA] Servidor '{server_name}' está instável!")
    print(f"⚠️ {metric} atingiu {value}%! Verificando logs de segurança...")
    # Aqui futuramente inserimos o requests.post() para a API do Telegram

@app.route('/api/monitor/v1/update', methods=['POST'])
def receive_metrics():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
        
    server_name = data.get("server_name", "Unknown_Node")
    cpu = data.get("cpu", 0)
    ram = data.get("ram", 0)
    
    # Armazena o histórico do nó
    if server_name not in server_history:
        server_history[server_name] = []
    server_history[server_name].append({"timestamp": time.time(), "cpu": cpu, "ram": ram})
    
    # Lógica de Deteção de Anomalias (Regra básica de Limiar)
    if cpu > 85:
        send_infrastructure_alert(server_name, "Uso de CPU", cpu)
    if ram > 90:
        send_infrastructure_alert(server_name, "Uso de Memória RAM", ram)
        
    return jsonify({"status": "success", "node": server_name, "received": True}), 200

@app.route('/api/events', methods=['POST'])
def create_operational_event():
    data = request.get_json(silent=True) or {}
    required = ["event_type", "description", "source_device", "operator", "location"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"status": "error", "message": "Missing fields", "fields": missing}), 400

    event_id = data.get("event_id") or f"REX-EVT-{uuid.uuid4().hex[:12].upper()}"
    event = OperationalEvent.create(
        event_id=event_id,
        event_type=data["event_type"],
        description=data["description"],
        source_device=data["source_device"],
        operator=data["operator"],
        location=data["location"],
        payload=data.get("payload", {}),
        created_at=data.get("created_at"),
    )
    event_engine.enqueue(event)
    return jsonify({"status": "success", "data": event.to_dict()}), 201


@app.route('/api/events', methods=['GET'])
def list_operational_events():
    return jsonify({"status": "success", "data": [event.to_dict() for event in event_engine.all_events()]}), 200


@app.route('/api/events/sync', methods=['POST'])
def sync_operational_events():
    synced = event_engine.sync_pending(lambda event: bool(event.event_id and event.description))
    return jsonify({
        "status": "success",
        "synced": [event.to_dict() for event in synced if event.sync_status.value == "SYNCED"],
        "failed": [event.to_dict() for event in synced if event.sync_status.value == "FAILED"],
    }), 200


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
    active_nodes = {}
    for node, metrics in server_history.items():
        if metrics:
            active_nodes[node] = metrics[-1] # Pega a última métrica recebida
    return jsonify(active_nodes)

if __name__ == '__main__':
    # Roda o servidor na porta local 5000 do Termux
    app.run(host='0.0.0.0', port=5000, debug=True)

