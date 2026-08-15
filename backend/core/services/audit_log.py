"""Append-only audit log boundary for the REX proof of concept."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict


class JsonAuditLog:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.getenv("REX_AUDIT_STORE", "data/audit_log.json"))
        self._lock = threading.Lock()

    def record(self, *, actor: str, role: str, action: str, resource: str, result: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        entry = {
            "timestamp": time.time(),
            "actor": actor,
            "role": role,
            "action": action,
            "resource": resource,
            "result": result,
            "metadata": metadata or {},
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            records = []
            if self.path.exists():
                try:
                    records = json.loads(self.path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    records = []
            records.append(entry)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        return entry

    def all(self) -> list[Dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
