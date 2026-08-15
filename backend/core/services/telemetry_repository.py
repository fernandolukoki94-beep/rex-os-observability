"""Persistence boundary for infrastructure telemetry.

The JSON implementation is intentionally small and durable for the proof of
concept. A PostgreSQL adapter can implement the same protocol later without
changing Flask routes or the dashboard contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Protocol


class TelemetryRepository(Protocol):
    def append(self, server_name: str, sample: Dict[str, Any]) -> None: ...

    def latest_by_server(self) -> Dict[str, Dict[str, Any]]: ...

    def all(self) -> List[Dict[str, Any]]: ...


class JsonTelemetryRepository:
    """Atomic JSON-backed repository for infrastructure metric history."""

    def __init__(self, store_path: str = "data/telemetry_history.json") -> None:
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.store_path.exists():
            return []
        try:
            value = json.loads(self.store_path.read_text(encoding="utf-8"))
            return value if isinstance(value, list) else []
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _save(self) -> None:
        temporary = self.store_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self._records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(self.store_path)

    def append(self, server_name: str, sample: Dict[str, Any]) -> None:
        self._records.append({"server_name": server_name, **sample})
        self._save()

    def latest_by_server(self) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for record in self._records:
            server_name = str(record.get("server_name", "Unknown_Node"))
            latest[server_name] = {key: value for key, value in record.items() if key != "server_name"}
        return latest

    def all(self) -> List[Dict[str, Any]]:
        return list(self._records)
