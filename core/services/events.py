"""Domain objects for REX Mine Intelligence operational events.

The module is deliberately independent from Flask so it can be reused by an
edge agent, a simulator, tests, or a future persistent adapter.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class SyncStatus(str, Enum):
    PENDING = "PENDING"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class EvidenceEntry:
    event: str
    recorded_at: str
    detail: str


@dataclass
class OperationalEvent:
    event_id: str
    event_type: str
    description: str
    source_device: str
    operator: str
    created_at: str
    location: str
    payload: Dict[str, Any]
    integrity_hash: str
    sync_status: SyncStatus = SyncStatus.PENDING
    evidence: List[EvidenceEntry] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        event_id: str,
        event_type: str,
        description: str,
        source_device: str,
        operator: str,
        location: str,
        payload: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
    ) -> "OperationalEvent":
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        body = {
            "event_id": event_id,
            "event_type": event_type,
            "description": description,
            "source_device": source_device,
            "operator": operator,
            "created_at": timestamp,
            "location": location,
            "payload": payload or {},
        }
        fingerprint = hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        event = cls(
            **body,
            integrity_hash=fingerprint,
            evidence=[],
        )
        event.add_evidence("EVENT_CREATED", "Operational event created at edge")
        event.add_evidence("LOCAL_STORED", "Event persisted in the local queue")
        event.add_evidence("HASH_CREATED", "SHA-256 integrity fingerprint generated")
        return event

    def add_evidence(self, event: str, detail: str) -> None:
        self.evidence.append(
            EvidenceEntry(
                event=event,
                recorded_at=datetime.now(timezone.utc).isoformat(),
                detail=detail,
            )
        )

    def transition(self, status: SyncStatus, detail: str) -> None:
        self.sync_status = status
        evidence_event = {
            SyncStatus.SYNCING: "SYNC_STARTED",
            SyncStatus.SYNCED: "SYNCED",
            SyncStatus.FAILED: "SYNC_FAILED",
            SyncStatus.PENDING: "SYNC_PENDING",
        }.get(status, status.value)
        self.add_evidence(evidence_event, detail)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["sync_status"] = self.sync_status.value
        data["evidence"] = [asdict(entry) for entry in self.evidence]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationalEvent":
        raw_evidence = data.get("evidence", [])
        evidence = [EvidenceEntry(**entry) for entry in raw_evidence]
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            description=data["description"],
            source_device=data["source_device"],
            operator=data["operator"],
            created_at=data["created_at"],
            location=data["location"],
            payload=data.get("payload", {}),
            integrity_hash=data["integrity_hash"],
            sync_status=SyncStatus(data.get("sync_status", SyncStatus.PENDING.value)),
            evidence=evidence,
        )
