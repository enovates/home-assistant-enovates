"""EnovatesEntity class."""

from __future__ import annotations

import dataclasses

from enovates_modbus.base import RegisterMap
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
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


def transform_entity_descriptions_per_port[T: EntityDescription](ports: list[int], per_port: list[T]) -> dict[int, list[T]]:
    """Transform a list of entity descriptions into their port specific variants, if needed."""
    multi_port = len(ports) > 1
    return {
        port: [
            dataclasses.replace(
                ed,
                key=f"{ed.key}_{port}",
                translation_key=f"{ed.translation_key}_mp",
                translation_placeholders={**(ed.translation_placeholders or {}), "port_nr": str(port)},
            )
            if multi_port
            else ed
            for ed in per_port
        ]
        for port in ports
    }
