# REX Mine Intelligence Demo

This guide demonstrates the complete local flow without requiring a paid service, private token or real industrial equipment.

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

The demonstration uses synthetic telemetry and a local acknowledgement flow. It does not claim a live connection to a mining operator, machine, MQTT broker or production database.
