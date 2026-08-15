from backend.edge.agent import EdgeAgent


class Source:
    def sample(self):
        return {"device": "PUMP-017", "vibration": 6.2}


def test_edge_agent_collects_syncs_and_reports_health():
    sent = []
    agent = EdgeAgent("edge-07", Source(), sender=lambda record: sent.append(record) or True)
    record = agent.collect()
    assert record["device_id"] == "edge-07"
    assert agent.health()["queue_depth"] == 1
    assert agent.sync_once() is True
    assert len(sent) == 1
    assert agent.health()["queue_depth"] == 0


def test_edge_agent_queue_survives_reload(tmp_path):
    path = tmp_path / "edge-queue.json"
    first = EdgeAgent("edge-08", Source(), queue_path=str(path))
    first.collect()
    restored = EdgeAgent("edge-08", Source(), queue_path=str(path))
    assert restored.health()["queue_depth"] == 1
