"""Local Edge Agent boundary for future field deployments.

This is intentionally transport-neutral: the current adapter remains synthetic,
while MQTT/OPC-UA/Modbus clients can be injected later behind the same methods.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class EdgeAgent:
    device_id: str
    source: Any
    sender: Callable[[dict], bool] | None = None
    queue: list[dict] = field(default_factory=list)
    queue_path: str | None = None

    def __post_init__(self) -> None:
        if self.queue_path:
            path = Path(self.queue_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                try:
                    self.queue = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, TypeError):
                    self.queue = []

    def _save(self) -> None:
        if not self.queue_path:
            return
        path = Path(self.queue_path)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.queue, indent=2), encoding="utf-8")
        temporary.replace(path)

    def collect(self) -> dict:
        sample = self.source.sample() if hasattr(self.source, "sample") else self.source()
        record = {"device_id": self.device_id, "sample": sample}
        self.queue.append(record)
        self._save()
        return record

    def sync_once(self) -> bool:
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
        return {
            "device_id": self.device_id,
            "queue_depth": len(self.queue),
            "transport": "injected" if self.sender else "offline-only",
            "status": "healthy" if self.sender or not self.queue else "degraded",
        }
