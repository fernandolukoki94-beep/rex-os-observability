# REX Mine Intelligence Demo

This guide demonstrates the complete local flow without requiring a paid service, private token or real industrial equipment.

## PUMP-017 operational story

Present the demo as one operational narrative rather than a collection of screens. All telemetry is synthetic and intended for portfolio validation.

| Time | Operational state | REX behaviour |
|---|---|---|
| 08:00 | PUMP-017 normal | Baseline telemetry is visible |
| 09:10 | Vibration increases | The simulator exposes a controlled anomaly sequence |
| 09:15 | Connectivity is lost | Toggle the Operations Center to `OFFLINE` |
| 09:17 | Local anomaly detected | The operator opens a new incident |
| 09:18 | Incident recorded | Event ID, fingerprint and Evidence Chain are stored locally |
| 10:05 | Connectivity restored | Toggle back to `ONLINE` and start synchronisation |
| 10:05 | REX sends event | React calls `POST /api/events` through the Flask contract |
| 10:05 | Server acknowledgement | Flask returns the event payload and evidence; UI records `ACKNOWLEDGED` |
| 10:06 | Event confirmed | The event is displayed as `SYNCED` in the Operations Center |


## Start the backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. python3 -m backend.core.rex_core
```

The Flask API is available at `http://127.0.0.1:5000`.

## Start the frontend

In a second terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://127.0.0.1:5173/` for the landing page and `/rex` for the Operations Center.

## Validate the API contract

```bash
curl http://127.0.0.1:5000/api/telemetry/mine
curl http://127.0.0.1:5000/api/telemetry/mine/pump-sequence
curl http://127.0.0.1:5000/api/events
```

Create an operational event:

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
```

The demonstration uses synthetic telemetry and a Flask API acknowledgement flow backed by the local JSON event store. It does not claim a live connection to a mining operator, machine, MQTT broker or production database. The server contract is real within the proof of concept; industrial integration, authentication and PostgreSQL remain future phases.
