# REX-OS audit

- Repository: fernandolukoki94-beep/rex-os-observability
- Base branch: main
- Feature branch: feature/mine-intelligence-v1
- Current implementation: minimal Flask core at core/rex_core.py and looping mock agent at agent/agent_mock.py.
- Existing core routes: POST /api/monitor/v1/update and GET /api/monitor/v1/status.
- Documentation drift: README/API/ARCHITECTURE advertise broader agent, TUI and /api/* endpoints that are not present in this checkout.
- Reuse decision: preserve existing infrastructure telemetry routes and add a separate core/services/events package rather than enlarging rex_core.py.
- v1 scope: OperationalEvent, offline queue, Evidence Chain, mine telemetry simulator, and additive API routes.
