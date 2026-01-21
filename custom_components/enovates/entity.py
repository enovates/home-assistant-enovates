"""EnovatesEntity class."""

from __future__ import annotations

from enovates_modbus.base import RegisterMap
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)


class EnovatesEntity(CoordinatorEntity[DataUpdateCoordinator[RegisterMap]]):
    """EnovatesEntity class."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator[RegisterMap]) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
        )
