"""Deterministic mine telemetry simulator for demos and tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class TelemetrySample:
    equipment_id: str
    equipment_type: str
    temperature: float
    vibration: float
    pressure: float
    rpm: int
    anomaly_detected: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "equipment_id": self.equipment_id,
            "equipment_type": self.equipment_type,
            "temperature": self.temperature,
            "vibration": self.vibration,
            "pressure": self.pressure,
            "rpm": self.rpm,
            "anomaly_detected": self.anomaly_detected,
        }


class MineSimulator:
    """Generate repeatable equipment data for a professional demonstration."""

    equipment = (
        ("PUMP-017", "pump"),
        ("TRUCK-021", "truck"),
        ("CONVEYOR-04", "conveyor"),
        ("GENERATOR-02", "generator"),
    )

    def samples(self) -> Iterable[TelemetrySample]:
        yield TelemetrySample("PUMP-017", "pump", 72.3, 3.1, 4.7, 1800)
        yield TelemetrySample("TRUCK-021", "truck", 68.0, 2.4, 0.0, 1500)
        yield TelemetrySample("CONVEYOR-04", "conveyor", 61.2, 1.9, 3.5, 1200)
        yield TelemetrySample("GENERATOR-02", "generator", 70.5, 2.2, 4.1, 1800)

    def pump_vibration_sequence(self) -> List[TelemetrySample]:
        values = [3.1, 3.4, 4.1, 4.9, 5.7, 6.2]
        return [
            TelemetrySample(
                "PUMP-017",
                "pump",
                72.3 + index * 0.4,
                vibration,
                4.7,
                1800,
                anomaly_detected=vibration >= 5.7,
            )
            for index, vibration in enumerate(values)
        ]

    @staticmethod
    def detect_anomaly(sample: TelemetrySample, vibration_threshold: float = 5.5) -> bool:
        return sample.vibration >= vibration_threshold
