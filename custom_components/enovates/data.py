"""Custom types for Enovates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enovates_modbus.base import RegisterMap
    from enovates_modbus.eno_one import EnoOneClient
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
    from homeassistant.loader import Integration


type EnovatesConfigEntry = ConfigEntry[EnovatesData]


@dataclass
class EnovatesData:
    """Data for the Enovates integration."""

    client: EnoOneClient
    integration: Integration
    coordinators: dict[type[RegisterMap], DataUpdateCoordinator[RegisterMap]]

    def coordinator[T: RegisterMap](self, register_map: type[T]) -> DataUpdateCoordinator[T]:
        """Get the coordinator for a Register Map type."""
        return self.coordinators[register_map]
