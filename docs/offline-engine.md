# REX Offline Engine

The REX Offline Engine is the edge-side reliability boundary for operational events. It is designed around the assumption that a mine field device may lose connectivity while an operator still needs to record an incident and preserve evidence.

## Current flow

```text
capture → validate → create event ID → fingerprint → local queue → sync attempt → acknowledgement
```

The current Python implementation persists events atomically in a local JSON store and de-duplicates by `event_id`. The React frontend also contains an IndexedDB-backed local store for the browser demonstration, with a resilient `localStorage` fallback.

## Integrity model

Each event carries an immutable identifier, operational payload, synchronisation state and an Evidence Chain. The SHA-256 value is an integrity fingerprint: it makes accidental or unauthorised payload changes detectable. It is not presented as cryptographic non-repudiation, identity authentication or proof of industrial safety.

## Synchronisation states

| State | Meaning |
|---|---|
| `LOCAL` | Captured locally and not yet queued |
| `PENDING` | Ready for a synchronisation attempt |
| `SYNCING` | Transport attempt is in progress |
| `SYNCED` | Acknowledged by the current local Core flow |
| `FAILED` | Attempt failed but remains retryable |

## Future durable storage

PostgreSQL is the planned system-of-record integration once a secured backend environment exists. Redis is optional and should only be introduced if measured queue throughput or distributed coordination requires it. Neither dependency is required by the current free-tier demonstration.

## Security boundary

Real sensors, MQTT brokers and gateways must be introduced behind an authenticated adapter with certificate management, replay protection, payload validation and audit logging. Synthetic telemetry is labelled as synthetic throughout the current demonstration.
