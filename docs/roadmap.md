# REX Mine Intelligence Roadmap

## Phase 1 — Portfolio foundation

Completed. The official repository now contains the React/Vite frontend, Flask backend, offline event engine, synthetic mine telemetry, tests and documentation. Luko MemoryOS remains a separate origin project.

## Phase 2 — Operational resilience

The next implementation increment should add a connectivity history model, incident filtering, CSV/JSON export and clearer equipment indicators. Retry backoff and manual retry should remain observable to the operator rather than hidden in background code.

## Phase 3 — Secure edge adapter

Introduce an adapter boundary for MQTT or a gateway only after the transport contract is specified. The adapter must validate schemas, authenticate devices, protect against replay, record delivery acknowledgements and expose health metrics. No real mine connection should be claimed without explicit authorisation.

## Phase 4 — Durable server integration

Evaluate PostgreSQL as the system of record and Redis only if measured workload justifies a distributed queue or coordination layer. Define idempotency keys, conflict resolution, retention, backup and recovery before connecting field devices.

## Phase 5 — Intelligence

Add anomaly detection first as explainable rules and statistical baselines. Future AI features should be optional, auditable and never replace operator judgement for safety-critical decisions.

## Delivery principle

Each phase must remain demonstrable on a free local environment, pass automated tests, update the README and preserve a clear distinction between synthetic proof-of-concept data and authorised operational data.
