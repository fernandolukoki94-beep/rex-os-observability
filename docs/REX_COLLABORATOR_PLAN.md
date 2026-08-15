# REX Mine Intelligence — Execution Plan

This document translates the collaborator recommendations into an executable, incremental plan for the single official repository: `rex-os-observability`.

## Product position

REX Mine Intelligence is presented as an **offline-first operational intelligence platform for industrial and mining environments**. It is a complementary digital layer for operational events, telemetry, evidence and synchronisation. It does not claim to replace PLC, SCADA, historians, maintenance systems or industrial safety systems.

The Luko MemoryOS repository remains a separate origin/legacy project. Its identity and history are preserved; no REX implementation depends on it at runtime.

## Target architecture

```text
rex-os-observability/
├── frontend/       React + TypeScript + Vite + Tailwind + offline UI
├── backend/        Python + Flask + operational domain
├── simulator/      Deterministic mine telemetry and PUMP-017 scenario
├── tests/          Backend contracts and frontend build checks
├── docs/           Architecture, API, demo, security and roadmap
└── deployment/     Vercel configuration and deployment notes
```

The current repository uses `backend/simulator` and `backend/tests` as the first safe migration step. A later layout pass may expose top-level `simulator/` and `tests/` aliases only if that improves discoverability without duplicating source files.

## Execution sequence

| Step | Implementation target | Acceptance criterion |
|---|---|---|
| 1 | Single monorepo | Frontend, backend, simulator, tests and docs are understandable from one README |
| 2 | Real browser/API contract | Browser submits an event to Flask, receives an ACK and marks the event `SYNCED` |
| 3 | Durable local state | Offline events survive reload and remain idempotent during retry |
| 4 | Server persistence boundary | Local JSON remains the free demo store; a repository interface prepares PostgreSQL without requiring it |
| 5 | PUMP-017 narrative demo | Normal → vibration increase → connectivity loss → local anomaly → offline event → reconnection → ACK |
| 6 | Security boundary | Synthetic data is labelled; real MQTT/gateway integration is not claimed without authorisation |
| 7 | Presentation package | README, demo guide, architecture, roadmap and an optional 8–10 page deck describe the same product |
| 8 | Deployment | Vercel project is linked to `rex-os-observability`, and deployment status is reported honestly |

## Progress status

| Recommendation | Status |
|---|---|
| Single professional monorepo | Implemented in `main` |
| Frontend ↔ Flask API contract | Implemented: React calls `POST /api/events` and `/api/events/sync` |
| Server ACK in Evidence Chain | Implemented in the Operations Center |
| Durable local queue | Implemented with the Flask JSON store and browser local persistence |
| PUMP-017 narrative | Documented and available through the deterministic simulator |
| Security boundary | Documented; synthetic data is clearly labelled |
| PostgreSQL/Redis | Future adapter; intentionally not required for the free proof of concept |
| MQTT/gateway | Future authorised integration; no credentials or real sensors used |
| Vercel official deployment | Configuration prepared; provider permission still needs confirmation |

## Current limitations

The current proof of concept does not include PostgreSQL, Redis, industrial MQTT, real sensor credentials, production authentication, multi-tenant isolation or safety-critical alerting. These are future engineering phases, not hidden capabilities.

## Definition of done for the next increment

The next increment is complete when the React Operations Center can create an event through the Flask API, handle offline failure without data loss, retry idempotently after connectivity returns, display the server acknowledgement in the Evidence Chain and pass automated backend tests plus a production frontend build.
