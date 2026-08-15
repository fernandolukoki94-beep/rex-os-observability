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
| Dashboard local | [`http://127.0.0.1:5173`](http://127.0.0.1:5173) | Frontend React/Vite oficial durante o desenvolvimento |
| API local | [`http://127.0.0.1:5000`](http://127.0.0.1:5000) | Backend Flask e contratos operacionais |

REX-OS é um sistema de observabilidade distribuída que evolui de telemetria de infraestrutura para inteligência operacional edge. As rotas de infraestrutura originais permanecem intactas; a `main` contém eventos operacionais offline, Evidence Chain, telemetria mineira determinística, um frontend React/Vite e um backend Flask no mesmo produto.

## Visual access

O dashboard web é servido pela rota `/` do Flask e consome os contratos do mesmo Core. A aplicação apresenta claramente que os dados são sintéticos e que a integração com sensores reais exige autorização e revisão de segurança. Para executar localmente:

```bash
PYTHONPATH=. python3 -m backend.core.rex_core
```

Depois abra `http://127.0.0.1:5000/`. Os endpoints JSON continuam disponíveis para integração e testes:

```text
http://127.0.0.1:5000/api/telemetry/mine
http://127.0.0.1:5000/api/telemetry/mine/pump-sequence
http://127.0.0.1:5000/api/events
```

## REX product architecture

The extension introduces a typed `OperationalEvent` with an event ID, type, description, source device, operator, timestamp, location, payload, integrity fingerprint, synchronisation status and evidence entries. The `OfflineEventEngine` persists events atomically in a local JSON store, de-duplicates event IDs and retries events in `FAILED` state.

The Evidence Chain records the following progression:

```text
EVENT_CREATED → LOCAL_STORED → HASH_CREATED → SYNC_PENDING
             → SYNC_STARTED → SYNCED
```

A failed transport remains retryable rather than disappearing. The SHA-256 value is described as an **integrity fingerprint**: it makes accidental or unauthorised payload changes detectable, but it is not presented as a complete security or non-repudiation system.

## Mine simulator

The simulator generates synthetic samples for `PUMP-017`, `TRUCK-021`, `CONVEYOR-04` and `GENERATOR-02`. The pump sequence intentionally moves vibration from `3.1` to `6.2` so the demonstration can show **“Anomaly detected”** without claiming that the equipment will fail.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/monitor/v1/update` | Existing infrastructure telemetry ingestion |
| `GET` | `/api/monitor/v1/status` | Existing latest-node status view |
| `POST` | `/api/events` | Create and locally queue an Operational Event |
| `GET` | `/api/events` | List persisted events and Evidence Chains |
| `POST` | `/api/events/sync` | Run the injected local Core acknowledgement flow |
| `GET` | `/api/telemetry/mine` | Return one synthetic sample per mine equipment item |
| `GET` | `/api/telemetry/mine/pump-sequence` | Return the controlled vibration anomaly sequence |

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

Current monorepo verification: **7 backend tests passed** and the frontend TypeScript/Vite production build succeeds. The suite covers event fingerprints, Evidence Chain entries, idempotent enqueue, durable reload, failed-sync retry, HTTP validation, API synchronisation, dashboard serving and controlled telemetry anomaly detection.

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
│   ├── agent/
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
    └── roadmap.md
```

The repository keeps the implementation additive: the original infrastructure routes remain available, while `frontend/` provides the React/Vite interface, `backend/` provides Flask and the operational domain, and `api/index.py` exposes the backend runtime to Vercel. PostgreSQL, Redis, production authentication and an industrial gateway remain future integrations and are not claimed as present.

## Next engineering step

The next safe step is to strengthen this single-repository application with an explicit edge adapter boundary, durable production storage, conflict resolution, authenticated acknowledgement and observability of the sync process. The current dashboard remains a free-tier proof of concept with synthetic data; authorised integration with real equipment requires a separate security and operational review.

## License

MIT. See [`LICENSE`](LICENSE).

**Author:** [Fernando Lukoki](https://github.com/fernandolukoki94-beep)
