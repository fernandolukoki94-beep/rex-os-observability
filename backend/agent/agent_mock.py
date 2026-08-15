import requests
import time
import random

# URL da nossa API local rodando no Termux
API_URL = "http://127.0.0.1:5000/api/monitor/v1/update"

print("🚀 REX-OS Agent Inicializado no Nó Remoto...")

while True:
    # Simula a leitura real do hardware do servidor
    # Vamos forçar um pico aleatório para testar o sistema de alertas
    metrics = {
        "server_name": "VPS-Producao-Katanga",
        "cpu": random.choice([20, 25, 30, 88, 15, 92]), # Simula oscilação com picos críticos
        "ram": random.randint(60, 75)
    }
    
    try:
        response = requests.post(API_URL, json=metrics, timeout=2)
        print(f"[{time.strftime('%H:%M:%S')}] Métricas enviadas. Status Core: {response.status_code}")
    except Exception as e:
        print(f"Erro ao conectar com o Core do REX-OS: {e}")
        
    time.sleep(3)

