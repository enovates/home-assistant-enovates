"""Platform for number integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from enovates_modbus.base import RegisterMap
from enovates_modbus.eno_one import (
    Diagnostics,
    EMSLimit,
)
from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, LOGGER
from .entity import EnovatesEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from enovates_modbus.eno_one import EnoOneClient
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .data import EnovatesConfigEntry


# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class EnovatesNumberEntityDescription[T: RegisterMap](NumberEntityDescription):
    """Enovates number entity description."""

    rm_type: type[T]
    get_value_fn: Callable[[EnoOneClient], Any]
    set_value_fn: Callable[[EnoOneClient, float], Any]


ENTITY_DESCRIPTIONS = (
    EnovatesNumberEntityDescription[EMSLimit](
        entity_category=EntityCategory.DIAGNOSTIC,
        key="ems_limit",
        name="EMS Limit",
        rm_type=EMSLimit,
        get_value_fn=lambda api: api.get_ems_limit(),
        set_value_fn=lambda api, value: api.set_ems_limit(int(value)),
        native_min_value=-1,
        native_max_value=32_000,
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EnovatesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    if not entry.runtime_data.ems_control:
        return

    diagnostics = await entry.runtime_data.clients[1].get_diagnostics()

    async_add_entities(
        EnovatesNumberEntity(
            diagnostics=diagnostics,
            coordinator=entry.runtime_data.coordinator(i, entity_description.rm_type),
            entity_description=entity_description,
            client=entry.runtime_data.clients[i],
        )
        for entity_description in ENTITY_DESCRIPTIONS
        for i in sorted(entry.runtime_data.clients.keys())
    )


class EnovatesNumberEntity[T: RegisterMap](EnovatesEntity, NumberEntity):
    """Enovates number class."""

    diagnostics: Diagnostics
    entity_description: EnovatesNumberEntityDescription
    client: EnoOneClient

    def __init__(
        self,
        diagnostics: Diagnostics,
        coordinator: DataUpdateCoordinator[T],
        entity_description: EnovatesNumberEntityDescription,
        client: EnoOneClient,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self.client = client
        self._device_id = diagnostics.serial_nr
        self._attr_unique_id = f"{diagnostics.serial_nr}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, diagnostics.serial_nr)},
            manufacturer=diagnostics.manufacturer,
            model="ENO one",
            name="ENO one",
            model_id=diagnostics.model_id,
            serial_number=diagnostics.serial_nr,
            sw_version=diagnostics.firmware_version,
        )

    async def async_added_to_hass(self) -> None:
        """Restore state from device."""
        await super().async_added_to_hass()
        self._attr_native_value = await self.entity_description.get_value_fn(self.client)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        old = self._attr_native_value
        await self.entity_description.set_value_fn(self.client, value)
        self._attr_native_value = await self.entity_description.get_value_fn(self.client)
        LOGGER.debug("async_set_native_value old=%s, value=%s, device=%s", old, value, self._attr_native_value)
