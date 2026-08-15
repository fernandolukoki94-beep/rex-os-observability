"""Local Edge Agent boundary for future field deployments.

This is intentionally transport-neutral: the current adapter remains synthetic,
while MQTT/OPC-UA/Modbus clients can be injected later behind the same methods.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable

from .sqlite_queue import SQLiteQueue


@dataclass
class EdgeAgent:
    device_id: str
    source: Any
    sender: Callable[[dict], bool] | None = None
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
        record = {"device_id": self.device_id, "sample": sample}
        if self._sqlite_store is not None:
            self._sqlite_store.append(record)
            self.queue = self._sqlite_store.all()
        else:
            self.queue.append(record)
            self._save()
        return record

    def sync_once(self) -> bool:
        if self._sqlite_store is not None:
            first = self._sqlite_store.peek()
            if first is None:
                self.queue = []
                return True
            if self.sender is None or not self.sender(first):
                return False
            self._sqlite_store.pop()
            self.queue = self._sqlite_store.all()
            return True
        if not self.queue:
            return True
        if self.sender is None:
            return False
        if self.sender(self.queue[0]):
            self.queue.pop(0)
            self._save()
            return True
        return False

    def health(self) -> dict:
        queue_depth = self._sqlite_store.depth() if self._sqlite_store is not None else len(self.queue)
        return {
            "device_id": self.device_id,
            "queue_depth": queue_depth,
            "transport": "injected" if self.sender else "offline-only",
            "status": "healthy" if self.sender or not self.queue else "degraded",
        }
