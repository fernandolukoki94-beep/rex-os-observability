# REX Edge Agent

O `EdgeAgent` é a boundary local entre uma fonte de telemetria e o core do REX. Na prova de conceito, a fonte pode ser sintética e o sender é injectável para permitir testes sem MQTT, OPC-UA, Modbus ou equipamento industrial real.

## Fila local

Por defeito, a fila continua em memória para manter a boundary simples. Quando `queue_path` termina em `.sqlite` ou `.db`, o agente usa o adaptador SQLite transaccional incluído no repositório. O adaptador activa WAL, `synchronous=FULL`, timeout de locking e operações FIFO em transacções curtas.

```python
agent = EdgeAgent(
    device_id="edge-kolwezi-01",
    source=synthetic_source,
    sender=send_to_rex,
    queue_path="data/edge_queue.sqlite",
)
```

O modo JSON continua disponível para compatibilidade com demonstrações antigas e é seleccionado por extensões como `.json`. A fila SQLite é agora o caminho recomendado para o Edge Agent porque sobrevive a reinícios e conserva `collect`, `sync_once` e `health` sem introduzir dependências externas. A retenção, a verificação periódica de integridade e a política de backup continuam a ser responsabilidades do deployment industrial.

## Retry e dead-letter

O `OfflineEventEngine` regista `retry_count`, `last_attempt`, `next_retry_at` e `failure_reason`. Depois de três falhas de transporte, o evento recebe `dead_letter=true` e uma evidência `DEAD_LETTER`; deixa de ser seleccionado pela fila normal até ser analisado por um operador.

A política actual é deliberadamente simples e visível para a demonstração. O Edge Agent usa SQLite para durabilidade local, enquanto o `OfflineEventEngine` mantém jitter, backoff, replay supervisionado e métricas de idade da fila. Uma evolução de produção deverá acrescentar retenção configurável, verificação de integridade e testes de concorrência durante reinícios.

## Limites de integração

`SyntheticTelemetryAdapter` é a única fonte incluída na POC. MQTT, OPC-UA e Modbus são boundaries futuras. A activação de qualquer gateway real exige identidade de dispositivo, TLS/mTLS, gestão de credenciais, allowlists, segmentação de rede e revisão de segurança operacional.
