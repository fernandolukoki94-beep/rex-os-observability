from backend.edge.agent import EdgeAgent
from backend.edge.sqlite_queue import SQLiteQueue


class Source:
    def __init__(self):
        self.value = 0

    def sample(self):
        self.value += 1
        return {"sequence": self.value}


def test_edge_restart_preserves_queue_and_reconciles_after_transport_returns(tmp_path):
    path = tmp_path / "restart.sqlite"
    first = EdgeAgent("edge-01", Source(), sender=None, queue_path=str(path))
    first.collect()
    first.collect()
    assert first.health()["queue_depth"] == 2
    first._sqlite_store.close()  # simulate process shutdown

    delivered = []
    restarted = EdgeAgent(
        "edge-01", Source(), sender=lambda record: delivered.append(record) or True, queue_path=str(path)
    )
    assert restarted.sync_once() is True
    assert restarted.sync_once() is True
    assert len(delivered) == 2
    assert restarted.health()["queue_depth"] == 0


def test_edge_rejected_transport_keeps_all_samples_for_later_retry(tmp_path):
    path = tmp_path / "partial-sync.sqlite"
    agent = EdgeAgent("edge-01", Source(), sender=lambda record: record["sample"]["sequence"] == 1, queue_path=str(path))
    for _ in range(3):
        agent.collect()

    assert agent.sync_once() is True
    assert agent.sync_once() is False
    assert agent.health()["queue_depth"] == 2
    assert SQLiteQueue(str(path)).integrity_check() is True


def test_sqlite_queue_handles_large_offline_accumulation(tmp_path):
    path = tmp_path / "large.sqlite"
    queue = SQLiteQueue(str(path))
    for sequence in range(10_000):
        queue.append({"device_id": "edge-01", "sample": {"sequence": sequence}})

    assert queue.depth() == 10_000
    assert queue.peek()["sample"]["sequence"] == 0
    assert queue.integrity_check() is True
    queue.close()
