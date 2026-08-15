"""Local Edge Agent boundary for future field deployments.

This is intentionally transport-neutral: the current adapter remains synthetic,
while MQTT/OPC-UA/Modbus clients can be injected later behind the same methods.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable

from .sqlite_queue import SQLiteQueue


@dataclass
class EdgeAgent:
    device_id: str
    source: Any
    sender: Callable[[dict], bool | dict[str, Any]] | None = None
    queue: list[dict] = field(default_factory=list)
    queue_path: str | None = None
    _sqlite_store: SQLiteQueue | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.queue_path and Path(self.queue_path).suffix.lower() in {".sqlite", ".db"}:
            self._sqlite_store = SQLiteQueue(self.queue_path)
            initial_queue = list(self.queue)
            if not self._sqlite_store.depth() and initial_queue:
                for record in initial_queue:
                    self._sqlite_store.append(record)
            self.queue = self._sqlite_store.all()
            return
        if self.queue_path:
            path = Path(self.queue_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                try:
                    self.queue = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, TypeError):
                    self.queue = []

    def _save(self) -> None:
        if self._sqlite_store is not None:
            self.queue = self._sqlite_store.all()
            return
        if not self.queue_path:
            return
        path = Path(self.queue_path)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.queue, indent=2), encoding="utf-8")
        temporary.replace(path)

    def collect(self) -> dict:
        sample = self.source.sample() if hasattr(self.source, "sample") else self.source()
        record = {
            "device_id": self.device_id,
            "sample": sample,
            "event_id": f"{self.device_id}:{uuid.uuid4().hex}",
        }
        record["integrity_hash"] = self._integrity_hash(record)
        if self._sqlite_store is not None:
            self._sqlite_store.append(record)
            self.queue = self._sqlite_store.all()
        else:
            self.queue.append(record)
            self._save()
        return record

    @staticmethod
    def _integrity_hash(record: dict[str, Any]) -> str:
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _ack_matches(record: dict[str, Any], result: bool | dict[str, Any]) -> bool:
        if isinstance(result, bool):
            return result
        if not isinstance(result, dict) or result.get("accepted") is not True:
            return False
        return (
            result.get("event_id") == record.get("event_id")
            and result.get("integrity_hash") == record.get("integrity_hash")
        )

    def sync_once(self) -> bool:
        first = self._sqlite_store.peek() if self._sqlite_store is not None else (
            self.queue[0] if self.queue else None
        )
        if first is None:
            self.queue = []
            return True
        if self.sender is None:
            return False
        result = self.sender(first)
        if not self._ack_matches(first, result):
            return False
        if self._sqlite_store is not None:
            removed = self._sqlite_store.pop_if_matches(first)
            self.queue = self._sqlite_store.all()
            return removed is not None
        if not self.queue or self.queue[0] is not first:
            return False
        self.queue.pop(0)
        self._save()
        return True

    def health(self) -> dict:
        queue_depth = self._sqlite_store.depth() if self._sqlite_store is not None else len(self.queue)
        return {
            "device_id": self.device_id,
            "queue_depth": queue_depth,
            "transport": "injected" if self.sender else "offline-only",
            "status": "healthy" if self.sender or not self.queue else "degraded",
        }
