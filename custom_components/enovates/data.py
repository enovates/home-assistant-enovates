"""Custom types for Enovates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enovates_modbus.base import RegisterMap
    from enovates_modbus.eno_one import EnoOneClient
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .helpers import EnovatesDUCoordinator


type EnovatesConfigEntry = ConfigEntry[EnovatesData]


@dataclass
class EnovatesData:
    """Data for the Enovates integration."""

    ems_control: bool
    clients: dict[int, EnoOneClient]
    integration: Integration
    coordinators: dict[tuple[int, type[RegisterMap]], EnovatesDUCoordinator]

    def coordinator[T: RegisterMap](self, device_id: int, register_map: type[T]) -> EnovatesDUCoordinator[T]:
        """Get the coordinator for a Register Map type."""
        return self.coordinators[(device_id, register_map)]
