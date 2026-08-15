"""Edge adapter boundary for synthetic and future industrial telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Protocol


class TelemetrySource(Protocol):
    def samples(self) -> Iterable[Dict[str, Any]]: ...


@dataclass
class SyntheticTelemetryAdapter:
    """Adapter used by the POC; replaceable by MQTT/OPC-UA/Modbus later."""

    source: Any

    def samples(self) -> Iterable[Dict[str, Any]]:
        for sample in self.source.samples():
            yield sample.to_dict() if hasattr(sample, "to_dict") else dict(sample)


class FutureIndustrialAdapter:
    """Explicit placeholder for an authorised industrial gateway integration."""

    def samples(self) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError("Industrial adapter requires an authorised gateway")
