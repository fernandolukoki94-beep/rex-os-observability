"""Offline-first queue for OperationalEvent objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from .events import OperationalEvent, SyncStatus


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
        if any(existing.event_id == event.event_id for existing in self._events):
            return next(existing for existing in self._events if existing.event_id == event.event_id)
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
            if event.sync_status in {SyncStatus.PENDING, SyncStatus.FAILED}
        ]

    def sync_pending(self, sender: Callable[[OperationalEvent], bool]) -> List[OperationalEvent]:
        results: List[OperationalEvent] = []
        for event in self.pending_events():
            event.transition(SyncStatus.SYNCING, "Connectivity available")
            self._save()
            try:
                accepted = sender(event)
            except Exception as exc:  # pragma: no cover - defensive edge boundary
                accepted = False
                detail = f"Transport error: {exc}"
            else:
                detail = "Core acknowledged event" if accepted else "Core rejected event"
            event.transition(SyncStatus.SYNCED if accepted else SyncStatus.FAILED, detail)
            self._save()
            results.append(event)
        return results

    def replace(self, events: Iterable[OperationalEvent]) -> None:
        self._events = list(events)
        self._save()

    def get(self, event_id: str) -> Optional[OperationalEvent]:
        return next((event for event in self._events if event.event_id == event_id), None)
