"""Optional PostgreSQL repository boundary.

The free/local MVP intentionally uses JsonTelemetryRepository. This adapter is
kept explicit so a production deployment can inject a real database client
without changing Flask route contracts.
"""

from __future__ import annotations


class PostgresTelemetryRepository:
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("A PostgreSQL DSN is required")
        self.dsn = dsn

    def append(self, server_name: str, sample: dict) -> None:
        raise NotImplementedError("PostgreSQL adapter is a documented production boundary; use JSON for the local POC")

    def latest_by_server(self) -> dict:
        raise NotImplementedError("PostgreSQL adapter is not enabled in the local POC")
