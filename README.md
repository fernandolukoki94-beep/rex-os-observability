# REX-OS v3 — Mine Intelligence Extension

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **Infrastructure Observability + Offline Edge + Operational Event Intelligence.**

# REX Mine Intelligence

> **REX Mine Intelligence is an offline-first operational intelligence platform for industrial and mining environments.**

Este é o repositório principal e completo de **Fernando Lucoco** para o produto REX. Contém frontend, backend, offline engine, telemetria, Evidence Chain, testes, documentação e deployment. O [Luko MemoryOS](https://github.com/fernandolukoki94-beep/luko-memoryos) permanece como projecto de origem/legado e não é necessário para executar o REX.

| Acesso | Link | Conteúdo |
|---|---|---|
| Código e documentação | [rex-os-observability](https://github.com/fernandolukoki94-beep/rex-os-observability) | Monorepo oficial do produto REX |
| Projecto de origem | [Luko MemoryOS](https://github.com/fernandolukoki94-beep/luko-memoryos) | Fundação React/Vite histórica, preservada separadamente |
| Dashboard live | [REX Mine Intelligence](https://rex-observability-main-git-main-fernandolukoki94-beeps-projects.vercel.app/) | Deployment Vercel do branch `main` |
| Health live | [`/api/health`](https://rex-observability-main-git-main-fernandolukoki94-beeps-projects.vercel.app/api/health) | Estado operacional público do Flask |
| Metrics live | [`/metrics`](https://rex-observability-main-git-main-fernandolukoki94-beeps-projects.vercel.app/metrics) | Métricas Prometheus públicas |
| Dashboard local | [`http://127.0.0.1:5173`](http://127.0.0.1:5173) | Frontend React/Vite oficial durante o desenvolvimento |
| API local | [`http://127.0.0.1:5000`](http://127.0.0.1:5000) | Backend Flask e contratos operacionais |

REX-OS é um sistema de observabilidade distribuída que evolui de telemetria de infraestrutura para inteligência operacional edge. As rotas de infraestrutura originais permanecem intactas; a `main` contém eventos operacionais offline, Evidence Chain, telemetria mineira determinística, um frontend React/Vite e um backend Flask no mesmo produto.

## Visual access

O produto tem duas superfícies no mesmo repositório: o fallback dashboard Flask em `/` e o Operations Center React em `frontend/`. O frontend usa um proxy Vite local para falar com o mesmo contrato Flask; em produção, o routing Vercel encaminha `/api` para a função Python. A aplicação apresenta claramente que os dados são sintéticos e que a integração com sensores reais exige autorização e revisão de segurança. Para executar localmente, inicie o backend e o frontend em terminais separados:

```bash
PYTHONPATH=. python3 -m backend.core.rex_core
cd frontend && pnpm install && pnpm dev
```

Depois abra `http://127.0.0.1:5173/` para o frontend ou `http://127.0.0.1:5000/` para o fallback Flask. Os endpoints JSON continuam disponíveis para integração e testes:

```text
http://127.0.0.1:5000/api/telemetry/mine
http://127.0.0.1:5000/api/telemetry/mine/pump-sequence
http://127.0.0.1:5000/api/events
```

## REX product architecture

The extension introduces a typed `OperationalEvent` with an event ID, type, description, source device, operator, timestamp, location, payload, integrity fingerprint, synchronisation status and evidence entries. The `OfflineEventEngine` persists events atomically in a local JSON store, de-duplicates identical event IDs, rejects same-ID/different-hash conflicts with `409`, and records `retry_count`, `last_attempt`, `next_retry_at`, `retry_delay_seconds` and `failure_reason`. Retry delays use bounded jitter to avoid synchronized retry bursts, and an event moves to `DEAD_LETTER` after three failed attempts. A supervised replay endpoint can re-queue a dead-letter event and append `DEAD_LETTER_REPLAYED` to its evidence. The EdgeAgent can persist its local queue atomically as JSON for compatibility or transactionally in SQLite when `queue_path` ends in `.sqlite` or `.db`. The SQLite adapter uses WAL, full synchronous commits, local locking and FIFO transactions without adding a cloud dependency.

The Evidence Chain records the following progression:

```text
EVENT_CREATED → LOCAL_STORED → HASH_CREATED → SYNC_PENDING
             → SYNC_STARTED → SYNCED
             └──────────────→ SYNC_FAILED → RETRY_SCHEDULED → DEAD_LETTER
                                              └────────────→ DEAD_LETTER_REPLAYED
```

Each event exposes an `integrity_hash`, a `previous_event_hash` and a derived `chain_hash`. New events reference the preceding event hash, while malformed or conflicting submissions are rejected rather than replacing existing evidence. The SHA-256 values are described as **integrity fingerprints**: they make accidental or unauthorised payload changes detectable, but they are not presented as a complete security or non-repudiation system.

## Mine simulator

The simulator generates synthetic samples for `PUMP-017`, `TRUCK-021`, `CONVEYOR-04` and `GENERATOR-02`. The pump sequence intentionally moves vibration from `3.1` to `6.2` so the demonstration can show **“Anomaly detected”** without claiming that the equipment will fail.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/monitor/v1/update` | Existing infrastructure telemetry ingestion |
| `GET` | `/api/monitor/v1/status` | Existing latest-node status view |
| `POST` | `/api/events` | Create, persist and queue an Operational Event; returns a server ACK payload |
| `GET` | `/api/events` | List persisted events and Evidence Chains |
| `POST` | `/api/events/sync` | Reconcile pending events through the Flask Core and return `SYNCED` events |
| `POST` | `/api/events/dead-letter/replay` | Supervised re-queue of one dead-letter event |
| `GET` | `/metrics` | Dependency-free Prometheus text metrics for API, queue, sync and dead-letter state |
| `GET` | `/api/telemetry/mine` | Return one synthetic sample per mine equipment item |
| `GET` | `/api/telemetry/mine/pump-sequence` | Return the controlled vibration anomaly sequence |
| `GET` | `/api/health` | Report REX runtime health, queue, storage, edge, telemetry and request trace identifier |
| `GET` | `/api/audit` | Return the append-only POC audit entries |

Example event:

```bash
curl -X POST http://127.0.0.1:5000/api/events \
  -H 'Content-Type: application/json' \
  -d '{
    "event_type": "EQUIPMENT_INCIDENT",
    "description": "Vibration above normal range",
    "source_device": "field-device-07",
    "operator": "operator-demo-01",
    "location": "Pit North",
    "payload": {"equipment_id": "PUMP-017", "vibration": 6.2}
  }'

curl -X POST http://127.0.0.1:5000/api/events/sync
curl http://127.0.0.1:5000/api/events
```

The React Operations Center follows the same contract: it stores the event locally first, attempts `POST /api/events` when connectivity is available, records the Flask acknowledgement in the Evidence Chain, and marks the event `SYNCED`. If the API is unavailable, the event remains retryable in the local queue.

```text
Browser → local queue → POST /api/events → Flask Core → ACK → SYNCED
                   └── offline / transport error → retryable queue
```

## Run locally

```bash
git clone https://github.com/fernandolukoki94-beep/rex-os-observability.git
cd rex-os-observability
git checkout main
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. python3 -m backend.core.rex_core
```

O backend Flask escuta em `http://127.0.0.1:5000` e o frontend React em `http://127.0.0.1:5173`. O event store local assume `data/offline_events.json`; defina `REX_EVENT_STORE` para usar outro caminho durante uma demonstração ou teste.

Para executar o frontend, abra um segundo terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

## Verification

```bash
PYTHONPATH=. python3 -m pytest -q backend/tests
python3 -m compileall backend api
cd frontend && pnpm run build
```

Current monorepo verification: **34 backend tests passed** in the local suite. The suite covers access control, audit, JSON and SQLite EdgeAgent persistence, telemetry repositories, atomic reload, retry metadata with jitter, supervised dead-letter replay, same-ID/different-hash conflict rejection, chained hashes, HTTP validation, API synchronisation, dashboard serving, controlled telemetry anomaly detection, REX Health, Prometheus metrics, request trace correlation, API-key failure cases and chaos scenarios for restart, rejected transport, SQLite integrity and 10,000 offline samples. The frontend TypeScript/Vite production build remains part of the verification contract.

## Structure

```text
rex-os-observability/
├── frontend/
│   ├── src/pages/RexLanding.tsx
│   ├── src/pages/RexOperations.tsx
│   ├── src/lib/rexOfflineStore.ts
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── core/
│   │   ├── rex_core.py
│   │   └── services/
│   ├── simulator/mine/
│   ├── edge/
│   │   ├── adapter.py
│   │   ├── agent.py
│   │   └── sqlite_queue.py  # transactional local queue
│   ├── tests/
│   └── requirements.txt
├── api/index.py
├── templates/index.html
├── vercel.json
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    ├── INSTALLATION.md
    ├── MINE_INTELLIGENCE_AUDIT.md
    ├── offline-engine.md
    ├── demo.md
    ├── roadmap.md
    ├── rex-health.md
    ├── failure-testing.md
    ├── observability-hardening.md
```

The repository keeps the implementation additive: the original infrastructure routes remain available, while `frontend/` provides the React/Vite interface, `backend/` provides Flask and the operational domain, and `api/index.py` exposes the backend runtime to Vercel. PostgreSQL, Redis, production authentication and an industrial gateway remain future integrations and are not claimed as present.

## Next engineering step

The next safe step is to evolve this single-repository application from hardened POC boundaries into production integrations: multi-process chaos testing, real authentication and device identity, PostgreSQL, retention and backup policies, and authorised MQTT/OPC-UA/Modbus gateways. SQLite Edge Queue, metrics, request trace correlation, retry jitter, dead-letter replay, conflict preservation, chained hashes and local disaster tests are now implemented without cost. The current dashboard remains a free-tier proof of concept with synthetic data; authorised integration with real equipment requires a separate security and operational review.

## License

MIT. See [`LICENSE`](LICENSE).

**Author:** [Fernando Lukoki](https://github.com/fernandolukoki94-beep)


## Novas salvaguardas de engenharia

A camada backend inclui agora `JsonTelemetryRepository`, uma boundary de persistência atómica para o histórico de infraestrutura. O adaptador JSON mantém a demonstração sem custos e pode ser substituído por PostgreSQL sem alterar as rotas Flask. O endpoint de eventos garante idempotência por `event_id`: a primeira submissão devolve `201`, enquanto uma repetição devolve `200` com `idempotent: true` e não duplica o evento.

No frontend, a fila operacional usa IndexedDB como armazenamento primário, com fallback para `localStorage` em browsers sem IndexedDB. Esta decisão preserva o funcionamento da demonstração e aproxima o fluxo do modelo `IndexedDB → local event store → queue → API` recomendado para a evolução do produto.

O Flask suporta uma API key opcional através da variável de ambiente `REX_API_KEY` e do cabeçalho `X-REX-API-Key`. Quando a variável não existe, o modo local continua acessível; quando é configurada no deployment, as rotas `/api` exigem autenticação básica de serviço. O modo `REX_RBAC_ENFORCED=1` activa papéis POC (`ADMIN`, `SUPERVISOR`, `OPERATOR`, `VIEWER`) e o `JsonAuditLog` regista actor, papel, acção, recurso e resultado. Isto é uma salvaguarda POC e não substitui autenticação industrial, RBAC de produção, gestão de segredos ou auditoria certificada.

O endpoint `/api/health` torna o próprio REX observável, reportando latência média, erros API, profundidade e idade da fila, falhas de sincronização, tamanho do armazenamento, adaptador de edge, fonte de telemetria, memória máxima do processo e `trace_id`. O endpoint `/metrics` expõe a mesma orientação operacional em formato Prometheus sem adicionar dependências: requests, erros, queue depth, queue age, eventos, syncs, tracing e dead-letters, com contadores de processo explicitamente documentados como process-scoped. O `EdgeAgent` suporta a fila transaccional SQLite através de `queue_path="data/edge_queue.sqlite"`; JSON permanece disponível para compatibilidade. `PostgresTelemetryRepository` está documentado como substituição futura do JSON; não é activado por defeito e não exige custos ou serviços externos na POC.

O directório `backend/edge/` define o boundary entre uma fonte de telemetria e o core REX. A implementação actual é `SyntheticTelemetryAdapter`; MQTT, OPC-UA e Modbus permanecem adaptadores futuros que só devem ser activados com gateway autorizado e revisão de segurança.
