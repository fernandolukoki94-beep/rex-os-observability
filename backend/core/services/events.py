"""Domain objects for REX Mine Intelligence operational events.

The module is deliberately independent from Flask so it can be reused by an
edge agent, a simulator, tests, or a future persistent adapter.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
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
    previous_event_hash: Optional[str] = None
    chain_hash: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.PENDING
    evidence: List[EvidenceEntry] = field(default_factory=list)
    retry_count: int = 0
    last_attempt: Optional[str] = None
    next_retry_at: Optional[str] = None
    failure_reason: Optional[str] = None
    retry_delay_seconds: Optional[float] = None
    dead_letter: bool = False

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
        event.rebuild_chain_hash()
        event.add_evidence("EVENT_CREATED", "Operational event created at edge")
        event.add_evidence("LOCAL_STORED", "Event persisted in the local queue")
        event.add_evidence("HASH_CREATED", "SHA-256 integrity fingerprint generated")
        return event

    def rebuild_chain_hash(self, previous_event_hash: Optional[str] = None) -> str:
        self.previous_event_hash = previous_event_hash
        chain_material = f"{previous_event_hash or ''}:{self.integrity_hash}".encode("utf-8")
        self.chain_hash = hashlib.sha256(chain_material).hexdigest()
        return self.chain_hash

    def add_evidence(self, event: str, detail: str) -> None:
        self.evidence.append(
            EvidenceEntry(
                event=event,
                recorded_at=datetime.now(timezone.utc).isoformat(),
                detail=detail,
            )
        )

    def schedule_retry(self, reason: str, max_retries: int = 3, jitter_ratio: float = 0.25) -> None:
        self.failure_reason = reason
        if self.retry_count >= max_retries:
            self.dead_letter = True
            self.next_retry_at = None
            self.retry_delay_seconds = None
            self.add_evidence("DEAD_LETTER", f"Retry limit reached after {self.retry_count} attempts: {reason}")
            return
        base_delay = 2 ** max(0, self.retry_count - 1)
        bounded_jitter = max(0.0, min(float(jitter_ratio), 1.0))
        delay_seconds = base_delay * (1 + random.uniform(-bounded_jitter, bounded_jitter))
        self.retry_delay_seconds = round(delay_seconds, 3)
        self.next_retry_at = (datetime.now(timezone.utc) + timedelta(seconds=self.retry_delay_seconds)).isoformat()
        self.add_evidence("RETRY_SCHEDULED", f"Retry scheduled in {self.retry_delay_seconds}s with jitter")

    def replay(self) -> None:
        """Re-queue a dead-letter event after an explicit supervised decision."""
        if not self.dead_letter:
            raise ValueError("event is not dead-lettered")
        self.dead_letter = False
        self.sync_status = SyncStatus.PENDING
        self.retry_count = 0
        self.last_attempt = None
        self.next_retry_at = None
        self.retry_delay_seconds = None
        self.failure_reason = None
        self.add_evidence("DEAD_LETTER_REPLAYED", "Dead-letter event re-queued by an authorised supervisor")

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
        event = cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            description=data["description"],
            source_device=data["source_device"],
            operator=data["operator"],
            created_at=data["created_at"],
            location=data["location"],
            payload=data.get("payload", {}),
            integrity_hash=data["integrity_hash"],
            previous_event_hash=data.get("previous_event_hash"),
            chain_hash=data.get("chain_hash"),
            sync_status=SyncStatus(data.get("sync_status", SyncStatus.PENDING.value)),
            evidence=evidence,
            retry_count=int(data.get("retry_count", 0)),
            last_attempt=data.get("last_attempt"),
            next_retry_at=data.get("next_retry_at"),
            failure_reason=data.get("failure_reason"),
            retry_delay_seconds=data.get("retry_delay_seconds"),
            dead_letter=bool(data.get("dead_letter", False)),
        )
        if not event.chain_hash:
            event.rebuild_chain_hash(event.previous_event_hash)
        return event
