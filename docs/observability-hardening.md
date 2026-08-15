# Observability Hardening

**Autor principal:** Fernando Lucoco

Esta fase acrescenta correlação operacional ao REX sem introduzir um SDK externo. Cada request recebe um `trace_id` a partir do header `X-REX-Trace-ID` ou, quando esse header não existe, de um identificador aleatório gerado pelo Flask. O valor é devolvido no mesmo header e, no endpoint `/api/health`, também aparece no campo `trace_id`.

> O `trace_id` é uma correlação de diagnóstico; não substitui autenticação, autorização, auditoria ou uma plataforma de tracing distribuído.

## Fluxo de correlação

```text
HTTP request
    |
    +-- X-REX-Trace-ID recebido ou gerado
    |
    +-- route Flask
    |
    +-- audit / persistência / sync
    |
    +-- X-REX-Trace-ID devolvido na resposta
```

O REX limita um trace recebido a 128 caracteres e não o utiliza como label Prometheus. Assim, a identificação de uma operação permanece disponível para logs e investigação sem criar cardinalidade ilimitada na superfície de métricas.

## Modelo de métricas

As métricas actuais devem ser lidas em duas categorias distintas:

| Categoria | Exemplos | Semântica |
|---|---|---|
| Processo | `rex_api_requests_total`, `rex_api_errors_total`, `rex_sync_success_total`, `rex_sync_failures_total`, `rex_trace_requests_total` | Contadores residentes no processo Flask; podem reiniciar a zero quando a instância reinicia ou é substituída |
| Domínio | `rex_events_total`, `rex_queue_depth`, `rex_queue_age_seconds`, `rex_dead_letter_events_total` | Estado calculado a partir dos eventos persistidos disponíveis naquela instância |

Em Vercel ou noutra plataforma serverless, a agregação histórica de contadores exige um colector externo ou uma camada de métricas persistente. O endpoint local não deve fingir que contadores de processo são globais.

## Contrato público

| Endpoint | Observabilidade |
|---|---|
| `/api/health` | Resumo dos componentes, estado da fila, idade, armazenamento, memória do processo e `trace_id` |
| `/metrics` | Formato Prometheus sem dependências externas, com explicação process-scoped nos `HELP` relevantes |
| Qualquer `/api/*` | Header de resposta `X-REX-Trace-ID` |

O próximo passo para uma instalação industrial seria exportar spans para um collector OpenTelemetry. Essa integração não faz parte desta POC para preservar o objectivo de custo zero e manter o motor independente de fornecedores.
