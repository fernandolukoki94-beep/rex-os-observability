from backend.core.services.telemetry_repository import JsonTelemetryRepository


def test_telemetry_repository_persists_and_reloads(tmp_path):
    path = tmp_path / "telemetry.json"
    repository = JsonTelemetryRepository(str(path))
    repository.append("PUMP-017", {"vibration": 6.2})
    reloaded = JsonTelemetryRepository(str(path))
    assert reloaded.latest_by_server()["PUMP-017"]["vibration"] == 6.2
