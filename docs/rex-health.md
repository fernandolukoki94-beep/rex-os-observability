# REX Health

O REX Observability também monitoriza o próprio runtime. O endpoint `GET /api/health` apresenta um snapshot leve e sem dependências externas sobre a saúde da API, do armazenamento, da fila offline, da sincronização, da fronteira edge e da fonte de telemetria.

| Componente | Indicadores actuais | Interpretação |
|---|---|---|
| API | Latência média dos últimos pedidos e erros HTTP | Saúde do contrato Flask |
| Database | Adaptador activo | `JsonTelemetryRepository` na POC; PostgreSQL é uma boundary futura |
| Queue | Profundidade pending/syncing e falhas | Pressão operacional da fila |
| Edge | Adaptador e estado | `SyntheticTelemetryAdapter` na demonstração |
| Sync | Eventos pendentes e failed | Capacidade de reconciliação |
| Storage | Número de eventos e bytes de telemetria | Crescimento do armazenamento local |
| Telemetry | Estado e origem | Sintética, claramente identificada |
| Process | Memória máxima reportada pelo processo | Sinal básico do runtime |

O endpoint não é uma ferramenta de observabilidade industrial completa. Numa implantação posterior, métricas históricas, tracing, alertas, retenção e dashboards externos devem ser adicionados com requisitos de segurança e operação definidos.

## Exemplo

```bash
curl http://127.0.0.1:5000/api/health
```
