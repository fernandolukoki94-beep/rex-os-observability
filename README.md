# REX-OS v3 — Mine Intelligence Extension

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **Infrastructure Observability + Offline Edge + Operational Event Intelligence.**

REX-OS Mine Intelligence é o portfólio único de **Fernando Lucoco**. Este mesmo repositório contém o Core Python/Flask, os contratos de eventos operacionais, o simulador de telemetria, o dashboard web e a demonstração offline-first. Não existe um segundo repositório necessário para compreender ou executar o projecto.

| Acesso | Link | Conteúdo |
|---|---|---|
| Código e documentação | [rex-os-observability](https://github.com/fernandolukoki94-beep/rex-os-observability) | Aplicação completa, arquitectura, testes e roadmap |
| Dashboard publicado | [Abrir REX Mine Intelligence](https://rex-mine-intelligence-web.vercel.app/) | Interface operacional servida pelo Flask deste repositório |
| API mineira | [`/api/telemetry/mine`](https://rex-mine-intelligence-web.vercel.app/api/telemetry/mine) | Snapshot sintético de equipamentos |

REX-OS é um sistema de observabilidade distribuída que evolui de telemetria de infraestrutura para inteligência operacional edge. As rotas de infraestrutura originais permanecem intactas; a extensão `feature/mine-intelligence-v1` acrescenta eventos operacionais offline, Evidence Chain, telemetria mineira determinística e uma interface visual no próprio Core.

## Visual access

O dashboard web é servido pela rota `/` do Flask e consome os contratos do mesmo Core. A aplicação apresenta claramente que os dados são sintéticos e que a integração com sensores reais exige autorização e revisão de segurança. Para executar localmente:

```bash
python3 -m core.rex_core
```

Depois abra `http://127.0.0.1:5000/`. Os endpoints JSON continuam disponíveis para integração e testes:

```text
http://127.0.0.1:5000/api/telemetry/mine
http://127.0.0.1:5000/api/telemetry/mine/pump-sequence
http://127.0.0.1:5000/api/events
```

## What changed in `feature/mine-intelligence-v1`

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
git checkout feature/mine-intelligence-v1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m core.rex_core
```

The Core listens on `http://127.0.0.1:5000`. The local event store defaults to `data/offline_events.json`; set `REX_EVENT_STORE` to use another path during a demo or test.

## Verification

```bash
python3 -m pytest -q
python3 -m compileall core simulator tests
```

Current branch verification: **6 tests passed**. The test suite covers event fingerprints, Evidence Chain entries, idempotent enqueue, durable reload, failed-sync retry, HTTP validation, API synchronisation and controlled telemetry anomaly detection.

## Structure

```text
rex-os-observability/
├── core/
│   ├── rex_core.py
│   └── services/
│       ├── events.py
│       └── offline_engine.py
├── simulator/mine/
│   └── telemetry.py
├── agent/agent_mock.py
├── api/index.py
├── templates/index.html
├── vercel.json
├── tests/
│   ├── test_mine_intelligence.py
│   └── test_api.py
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    ├── INSTALLATION.md
    └── MINE_INTELLIGENCE_AUDIT.md
```

The repository keeps the implementation additive: the original infrastructure routes remain available, while `templates/index.html` provides the visual dashboard and `api/index.py` exposes the same Flask application to Vercel. A production database, authentication layer and industrial gateway are intentionally not claimed as present.

## Next engineering step

The next safe step is to strengthen this single-repository application with an explicit edge adapter boundary, durable production storage, conflict resolution, authenticated acknowledgement and observability of the sync process. The current dashboard remains a free-tier proof of concept with synthetic data; authorised integration with real equipment requires a separate security and operational review.

## License

MIT. See [`LICENSE`](LICENSE).

**Author:** [Fernando Lukoki](https://github.com/fernandolukoki94-beep)
