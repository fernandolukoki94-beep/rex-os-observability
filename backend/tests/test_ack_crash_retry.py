from __future__ import annotations

import pytest

from backend.edge.agent import EdgeAgent


class Source:
    def sample(self):
        return {"temperature": 42}


class IdempotentReceiver:
    def __init__(self):
        self.accepted: dict[str, str] = {}
        self.attempts: list[str] = []
        self.effects: list[str] = []

    def send(self, record):
        event_id = record["event_id"]
        self.attempts.append(event_id)
        if event_id not in self.accepted:
            self.accepted[event_id] = record["integrity_hash"]
            self.effects.append(event_id)
            return {
                "accepted": True,
                "event_id": event_id,
                "integrity_hash": record["integrity_hash"],
                "deduplicated": False,
            }
        assert self.accepted[event_id] == record["integrity_hash"]
        return {
            "accepted": True,
            "event_id": event_id,
            "integrity_hash": record["integrity_hash"],
            "deduplicated": True,
        }


def test_ack_then_crash_before_pop_is_recovered_and_deduplicated(tmp_path):
    path = tmp_path / "edge.sqlite"
    receiver = IdempotentReceiver()
    crashed = {"value": False}

    def sender_crashes_after_ack(record):
        ack = receiver.send(record)
        if not crashed["value"]:
            crashed["value"] = True
            raise RuntimeError("simulated crash after ACK before queue removal")
        return ack

    agent = EdgeAgent("PUMP-017", Source(), sender=sender_crashes_after_ack, queue_path=str(path))
    record = agent.collect()

    with pytest.raises(RuntimeError, match="after ACK"):
        agent.sync_once()

    assert agent.health()["queue_depth"] == 1
    assert receiver.effects == [record["event_id"]]

    restarted = EdgeAgent("PUMP-017", Source(), sender=receiver.send, queue_path=str(path))
    assert restarted.sync_once() is True
    assert restarted.health()["queue_depth"] == 0
    assert receiver.effects == [record["event_id"]]
    assert receiver.attempts == [record["event_id"], record["event_id"]]
    assert restarted._sqlite_store is not None
    assert restarted._sqlite_store.integrity_check() is True


def test_invalid_ack_cannot_remove_head(tmp_path):
    path = tmp_path / "edge.sqlite"
    agent = EdgeAgent(
        "PUMP-017",
        Source(),
        sender=lambda record: {
            "accepted": True,
            "event_id": "another-event",
            "integrity_hash": record["integrity_hash"],
        },
        queue_path=str(path),
    )
    agent.collect()

    assert agent.sync_once() is False
    assert agent.health()["queue_depth"] == 1

    reloaded = EdgeAgent("PUMP-017", Source(), sender=None, queue_path=str(path))
    assert reloaded.health()["queue_depth"] == 1
    assert reloaded._sqlite_store is not None
    assert reloaded._sqlite_store.integrity_check() is True
