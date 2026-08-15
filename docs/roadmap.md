# REX Mine Intelligence Roadmap

## Phase 1 — Portfolio foundation

Completed. The official repository now contains the React/Vite frontend, Flask backend, offline event engine, synthetic mine telemetry, tests and documentation. Luko MemoryOS remains a separate origin project.

## Phase 2 — REX production foundation

In progress. The runtime exposes `/api/health` with API latency, error count, queue depth, failed synchronisations, storage size, edge adapter, synthetic telemetry status and a request `trace_id`. The backend includes POC RBAC, append-only audit entries, API-key failure tests, retry metadata with bounded jitter, dead-letter replay, conflict detection, chained hashes, Prometheus-compatible metrics and disaster tests. New dashboard pages are deliberately deferred until the reliability core is stronger.

## Phase 3 — Durable server integration

The repository boundary is ready for `PostgresTelemetryRepository`, while `JsonTelemetryRepository` remains the default free/local adapter. The Edge Agent now supports a transactional `SQLiteQueue` selected with a `.sqlite` or `.db` path; the JSON mode remains available for backwards-compatible demonstrations. Production work must still define retention, backup, multi-process recovery and a managed database before field devices are connected.

## Phase 4 — Secure edge adapter

Introduce an adapter boundary for MQTT or a gateway only after the transport contract is specified. The adapter must validate schemas, authenticate devices, protect against replay, record delivery acknowledgements and expose health metrics. No real mine connection should be claimed without explicit authorisation.

## Phase 5 — Identity and audit

The POC exposes optional API-key protection and roles (`ADMIN`, `SUPERVISOR`, `OPERATOR`, `VIEWER`) behind `REX_RBAC_ENFORCED=1`, plus a JSON audit boundary. Production requires managed identity, role assignment, secret rotation, resource-level authorization and tamper-evident audit retention.

## Phase 6 — Reliability and intelligence

Before predictive intelligence, complete Prometheus-compatible metrics, conflict-preserving Evidence Chain evolution, replayable dead-letter events, disaster testing and authenticated device identity. Add anomaly detection first as explainable rules and statistical baselines. Future AI features should be optional, auditable and never replace operator judgement for safety-critical decisions.

## Next engineering sequence

The completed motor sequence is: metrics and queue age; retry jitter; supervised dead-letter replay; same-ID/different-hash conflict preservation; chained Evidence Chain entries; transactional SQLite Edge Queue; and request-level trace correlation. The next proof is chaos testing for restart, rejected sends, corruption, duplicate delivery and ACK loss. Real authentication, device identity, PostgreSQL and authorised industrial gateways remain later phases. Each step must remain independently testable and reversible.

## Delivery principle

Each phase must remain demonstrable on a free local environment, pass automated tests, update the README and preserve a clear distinction between synthetic proof-of-concept data and authorised operational data.
