"""Platform for sensor integration."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo

from enovates_modbus.base import RegisterMap
from enovates_modbus.eno_one import (
    CurrentOffered,
    Diagnostics,
    LockState,
    Mode3Details,
    Mode3State,
    State,
)

from .const import DOMAIN
from .entity import EnovatesEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .data import EnovatesConfigEntry


@dataclass(frozen=True, kw_only=True)
class EnovatesBinarySensorEntityDescription[T: RegisterMap](BinarySensorEntityDescription):
    """Enovates binary sensor entity description."""

    rm_type: type[T]
    value_fn: Callable[[T], Any]


def _entity_descriptions(
    ports: list[int],
) -> tuple[list[EnovatesBinarySensorEntityDescription], dict[int, list[EnovatesBinarySensorEntityDescription]]]:
    shared = [
        EnovatesBinarySensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="ocpp_state",
            name="OCPP connected",
            rm_type=State,
            value_fn=lambda data: data.ocpp_state,
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ),
        EnovatesBinarySensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="load_shedding_state",
            name="Load shedding",
            rm_type=State,
            value_fn=lambda data: data.load_shedding_state,
            device_class=BinarySensorDeviceClass.POWER,
        ),
    ]

    per_port = [
        EnovatesBinarySensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="locked",
            name="Locked",
            icon="mdi:lock-question",
            rm_type=State,
            value_fn=lambda data: data.lock_state != LockState.LOCKED,
            device_class=BinarySensorDeviceClass.LOCK,
        ),
        EnovatesBinarySensorEntityDescription[State](
            key="contactor_state",
            name="Applying power",
            rm_type=State,
            value_fn=lambda data: data.contactor_state,
            device_class=BinarySensorDeviceClass.POWER,
        ),
        EnovatesBinarySensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="car_connected",
            name="Car connected",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_num not in {Mode3State.A1, Mode3State.A2},
            device_class=BinarySensorDeviceClass.PLUG,
        ),
        EnovatesBinarySensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="car_requesting_power",
            name="Car requesting power",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_num in {Mode3State.C1, Mode3State.C2},
            device_class=BinarySensorDeviceClass.POWER,
        ),
        EnovatesBinarySensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="evse_fault",
            name="EVSE fault",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_num in {Mode3State.E, Mode3State.F},
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        EnovatesBinarySensorEntityDescription[CurrentOffered](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="evse_offering_power",
            name="EVSE offering power",
            rm_type=CurrentOffered,
            value_fn=lambda data: data.active_current_offered > 0,
            device_class=BinarySensorDeviceClass.POWER,
        ),
    ]

    multi_port = len(ports) > 1

    return shared, {
        port: [dataclasses.replace(ed, key=f"{ed.key}_{port}", name=f"{ed.name} Port {port}") if multi_port else ed for ed in per_port]
        for port in ports
    }


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EnovatesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    shared, per_port = _entity_descriptions(sorted(entry.runtime_data.clients.keys()))

    diagnostics = await entry.runtime_data.clients[1].get_diagnostics()

    async_add_entities(
        EnovatesBinarySensor(
            diagnostics=diagnostics,
            coordinator=entry.runtime_data.coordinator(1, ed.rm_type),
            entity_description=ed,
        )
        for ed in shared
    )

    for device_id, eds in per_port.items():
        async_add_entities(
            EnovatesBinarySensor(
                diagnostics=diagnostics,
                coordinator=entry.runtime_data.coordinator(device_id, ed.rm_type),
                entity_description=ed,
            )
            for ed in eds
        )


class EnovatesBinarySensor[T: RegisterMap](EnovatesEntity, BinarySensorEntity):
    """Enovates Binary Sensor class."""

    entity_description: EnovatesBinarySensorEntityDescription[T]

    def __init__(
        self,
        diagnostics: Diagnostics,
        coordinator: DataUpdateCoordinator[T],
        entity_description: EnovatesBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
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

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self.entity_description.value_fn(self.coordinator.data)
