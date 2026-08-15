"""Local Edge Agent boundary for future field deployments.

This is intentionally transport-neutral: the current adapter remains synthetic,
while MQTT/OPC-UA/Modbus clients can be injected later behind the same methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class EdgeAgent:
    device_id: str
    source: Any
    sender: Callable[[dict], bool] | None = None
    queue: list[dict] = field(default_factory=list)

    def collect(self) -> dict:
        sample = self.source.sample() if hasattr(self.source, "sample") else self.source()
        record = {"device_id": self.device_id, "sample": sample}
        self.queue.append(record)
        return record

    def sync_once(self) -> bool:
        if not self.queue:
            return True
        if self.sender is None:
            return False
        if self.sender(self.queue[0]):
            self.queue.pop(0)
            return True
        return False

    def health(self) -> dict:
        return {
            "device_id": self.device_id,
            "queue_depth": len(self.queue),
            "transport": "injected" if self.sender else "offline-only",
            "status": "healthy" if self.sender or not self.queue else "degraded",
        }
