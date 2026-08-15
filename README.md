# REX-OS v3 — Mine Intelligence Extension

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **Infrastructure Observability + Offline Edge + Operational Event Intelligence.**

REX-OS is a lightweight distributed observability system evolving from infrastructure telemetry into an industrial edge proof of concept. The original infrastructure routes remain intact; the `feature/mine-intelligence-v1` branch adds a separate Python domain layer for offline operational events, evidence timelines and deterministic mine telemetry.

## Visual access

The Python extension is an API-first system and does not yet ship a hosted web dashboard. Run the Core locally and inspect the JSON endpoints with a browser or `curl`:

```text
http://127.0.0.1:5000/api/telemetry/mine
http://127.0.0.1:5000/api/telemetry/mine/pump-sequence
http://127.0.0.1:5000/api/events
```

A visual dashboard belongs to a later layer. This branch intentionally proves the event engine and contracts first instead of publishing a fake industrial UI.

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
├── tests/
│   ├── test_mine_intelligence.py
│   └── test_api.py
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    ├── INSTALLATION.md
    └── MINE_INTELLIGENCE_AUDIT.md
```

The repository documentation predates the current minimal checkout and advertises components that are not present in this snapshot. `docs/MINE_INTELLIGENCE_AUDIT.md` records that drift explicitly. This extension keeps the implementation additive and avoids pretending that an absent TUI, database or production authentication layer already exists.

## Next engineering step

The next safe step is a field-facing adapter or web dashboard consuming these contracts. It should be developed after the Python event engine has been reviewed, not by expanding `core/rex_core.py` into a monolith. Production work would still require authentication, durable database design, conflict resolution, observability of the sync process, security review and authorised integration with real equipment.

## License

MIT. See [`LICENSE`](LICENSE).

**Author:** [Fernando Lukoki](https://github.com/fernandolukoki94-beep)
