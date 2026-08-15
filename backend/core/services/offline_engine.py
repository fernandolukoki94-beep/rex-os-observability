"""Offline-first queue for OperationalEvent objects."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional

from .events import OperationalEvent, SyncStatus


class EventConflictError(ValueError):
    """Raised when an event ID is reused with a different integrity hash."""


class OfflineEventEngine:
    """Persist events locally and synchronise them through an injected sender."""

    def __init__(self, store_path: str = "data/offline_events.json") -> None:
        self.store_path = Path(store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self._events: List[OperationalEvent] = self._load()

    def _load(self) -> List[OperationalEvent]:
        if not self.store_path.exists():
            return []
        try:
            raw = json.loads(self.store_path.read_text(encoding="utf-8"))
            return [OperationalEvent.from_dict(item) for item in raw]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            # A corrupt edge store must not crash the agent. The caller can
            # inspect the file and recover it separately.
            return []

    def _save(self) -> None:
        temporary = self.store_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps([event.to_dict() for event in self._events], indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.store_path)

    def enqueue(self, event: OperationalEvent) -> OperationalEvent:
        existing = next((item for item in self._events if item.event_id == event.event_id), None)
        if existing is not None:
            if existing.integrity_hash != event.integrity_hash:
                raise EventConflictError(event.event_id)
            return existing
        previous_hash = self._events[-1].chain_hash if self._events else None
        event.rebuild_chain_hash(previous_hash)
        event.transition(SyncStatus.PENDING, "Waiting for connectivity")
        self._events.append(event)
        self._save()
        return event

    def all_events(self) -> List[OperationalEvent]:
        return list(self._events)

    def pending_events(self) -> List[OperationalEvent]:
        return [
            event
            for event in self._events
            if event.sync_status in {SyncStatus.PENDING, SyncStatus.FAILED} and not event.dead_letter
        ]

    def sync_pending(self, sender: Callable[[OperationalEvent], bool]) -> List[OperationalEvent]:
        results: List[OperationalEvent] = []
        for event in self.pending_events():
            event.retry_count += 1
            event.last_attempt = datetime.now(timezone.utc).isoformat()
            event.transition(SyncStatus.SYNCING, f"Connectivity available; attempt #{event.retry_count}")
            self._save()
            try:
                accepted = sender(event)
            except Exception as exc:  # pragma: no cover - defensive edge boundary
                accepted = False
                detail = f"Transport error: {exc}"
            else:
                detail = "Core acknowledged event" if accepted else "Core rejected event"
            if accepted:
                event.failure_reason = None
                event.next_retry_at = None
                event.transition(SyncStatus.SYNCED, detail)
            else:
                event.transition(SyncStatus.FAILED, detail)
                event.schedule_retry(detail)
            self._save()
            results.append(event)
        return results

    def replay_dead_letter(self, event_id: str) -> OperationalEvent:
        event = self.get(event_id)
        if event is None:
            raise KeyError(event_id)
        event.replay()
        self._save()
        return event

    def replace(self, events: Iterable[OperationalEvent]) -> None:
        self._events = list(events)
        self._save()

    def get(self, event_id: str) -> Optional[OperationalEvent]:
        return next((event for event in self._events if event.event_id == event_id), None)
