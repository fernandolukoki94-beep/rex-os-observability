# REX Edge Agent

O `EdgeAgent` é a boundary local entre uma fonte de telemetria e o core do REX. Na prova de conceito, a fonte pode ser sintética e o sender é injectável para permitir testes sem MQTT, OPC-UA, Modbus ou equipamento industrial real.

## Fila local

Por defeito, a fila existe em memória para manter o exemplo simples. Para uma demonstração de recuperação após reinício, configure `queue_path` ao criar o agente. A fila é então serializada em JSON e escrita com `tmp + replace`, evitando que uma escrita parcial substitua o ficheiro principal.

```python
agent = EdgeAgent(
    device_id="edge-kolwezi-01",
    source=synthetic_source,
    sender=send_to_rex,
    queue_path="data/edge_queue.json",
)
```

Esta fila JSON é uma solução de POC sem custos. Uma instalação industrial deve substituí-la por uma fila local transaccional, como SQLite, com retenção, locking, verificação de integridade e política de recuperação testada.

## Retry e dead-letter

O `OfflineEventEngine` regista `retry_count`, `last_attempt`, `next_retry_at` e `failure_reason`. Depois de três falhas de transporte, o evento recebe `dead_letter=true` e uma evidência `DEAD_LETTER`; deixa de ser seleccionado pela fila normal até ser analisado por um operador.

A política actual é deliberadamente simples e visível para a demonstração. Uma evolução de produção deverá incluir um worker agendado, jitter, backoff configurável, reprocessamento autorizado da dead-letter queue e métricas de idade da fila.

## Limites de integração

`SyntheticTelemetryAdapter` é a única fonte incluída na POC. MQTT, OPC-UA e Modbus são boundaries futuras. A activação de qualquer gateway real exige identidade de dispositivo, TLS/mTLS, gestão de credenciais, allowlists, segmentação de rede e revisão de segurança operacional.
