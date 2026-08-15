from backend.edge.agent import EdgeAgent


class Source:
    def __init__(self):
        self.value = 0

    def sample(self):
        self.value += 1
        return {"temperature": self.value}


def test_sqlite_edge_queue_survives_reload_and_sync(tmp_path):
    path = tmp_path / "edge.sqlite"
    agent = EdgeAgent("PUMP-017", Source(), sender=lambda record: True, queue_path=str(path))

    first = agent.collect()
    second = agent.collect()
    assert first["sample"]["temperature"] == 1
    assert second["sample"]["temperature"] == 2
    assert agent.health()["queue_depth"] == 2

    reloaded = EdgeAgent("PUMP-017", Source(), sender=lambda record: True, queue_path=str(path))
    assert reloaded.health()["queue_depth"] == 2
    assert reloaded.sync_once() is True
    assert reloaded.health()["queue_depth"] == 1
    assert reloaded._sqlite_store is not None
    assert reloaded._sqlite_store.integrity_check() is True


def test_sqlite_edge_queue_keeps_head_when_sender_rejects(tmp_path):
    path = tmp_path / "edge.sqlite"
    agent = EdgeAgent("PUMP-017", Source(), sender=lambda record: False, queue_path=str(path))
    agent.collect()

    assert agent.sync_once() is False
    assert agent.health()["queue_depth"] == 1
    reloaded = EdgeAgent("PUMP-017", Source(), sender=None, queue_path=str(path))
    assert reloaded.health()["queue_depth"] == 1
