from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Banco de dados em memória temporário para o histórico de métricas
server_history = {}

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

