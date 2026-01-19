"""Platform for sensor integration."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.helpers.device_registry import DeviceInfo

from enovates_modbus.base import RegisterMap
from enovates_modbus.eno_one import (
    APIVersion,
    CurrentOffered,
    Diagnostics,
    EMSLimit,
    LEDColor,
    LockState,
    Measurements,
    Mode3Details,
    Mode3State,
    State,
    TransactionToken,
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
class EnovatesSensorEntityDescription[T: RegisterMap](SensorEntityDescription):
    """Enovates sensor entity description."""

    rm_type: type[T]
    value_fn: Callable[[T], Any]

    device_id: int | None = None


def _entity_descriptions(
    ports: list[int], *, ems_control: bool
) -> tuple[list[EnovatesSensorEntityDescription], dict[int, list[EnovatesSensorEntityDescription]]]:
    shared = [
        EnovatesSensorEntityDescription[APIVersion](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="api_version",
            name="API version",
            icon="mdi:format-quote-close",
            rm_type=APIVersion,
            value_fn=lambda data: f"{data.major}.{data.minor}",
        ),
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="max_amp_per_phase",
            name="Max amps per phase",
            rm_type=State,
            value_fn=lambda data: data.max_amp_per_phase,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="installation_current_l1",
            name="Installation Current L1",
            rm_type=Measurements,
            value_fn=lambda data: data.installation_current_l1,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="installation_current_l2",
            name="Installation Current L2",
            rm_type=Measurements,
            value_fn=lambda data: data.installation_current_l2,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="installation_current_l3",
            name="Installation Current L3",
            rm_type=Measurements,
            value_fn=lambda data: data.installation_current_l3,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="manufacturer",
            name="Manufacturer",
            rm_type=Diagnostics,
            value_fn=lambda data: data.manufacturer,
            icon="mdi:factory",
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="vendor_id",
            name="Vendor Id",
            rm_type=Diagnostics,
            value_fn=lambda data: data.vendor_id,
            icon="mdi:factory",
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="serial_nr",
            name="Serial Nr",
            rm_type=Diagnostics,
            value_fn=lambda data: data.serial_nr,
            icon="mdi:identifier",
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="model_id",
            name="Model Id",
            rm_type=Diagnostics,
            value_fn=lambda data: data.model_id,
            icon="mdi:identifier",
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="firmware_version",
            name="Firmware Version",
            rm_type=Diagnostics,
            value_fn=lambda data: data.firmware_version,
            icon="mdi:format-quote-close",
        ),
    ]

    per_port = [
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="number_of_phases",
            name="Number of phases",
            icon="mdi:transmission-tower",
            rm_type=State,
            value_fn=lambda data: data.number_of_phases,
        ),
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="lock_state",
            name="Lock state",
            icon="mdi:lock-question",
            rm_type=State,
            value_fn=lambda data: data.lock_state.name,
            device_class=SensorDeviceClass.ENUM,
            options=[s.name for s in LockState],
        ),
        EnovatesSensorEntityDescription[State](
            key="led_color",
            name="LED color",
            icon="mdi:led-on",
            rm_type=State,
            value_fn=lambda data: data.led_color.name,
            device_class=SensorDeviceClass.ENUM,
            options=[s.name for s in LEDColor],
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="current_l1",
            name="Current L1",
            rm_type=Measurements,
            value_fn=lambda data: data.current_l1,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="current_l2",
            name="Current L2",
            rm_type=Measurements,
            value_fn=lambda data: data.current_l2,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="current_l3",
            name="Current L3",
            rm_type=Measurements,
            value_fn=lambda data: data.current_l3,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="voltage_l1",
            name="Voltage L1",
            rm_type=Measurements,
            value_fn=lambda data: data.voltage_l1,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="voltage_l2",
            name="Voltage L2",
            rm_type=Measurements,
            value_fn=lambda data: data.voltage_l2,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="voltage_l3",
            name="Voltage L3",
            rm_type=Measurements,
            value_fn=lambda data: data.voltage_l3,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Measurements](
            key="charger_active_power_total",
            name="Chargering Power",
            rm_type=Measurements,
            value_fn=lambda data: data.charger_active_power_total,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="charger_active_power_l1",
            name="Chargering Power L1",
            rm_type=Measurements,
            value_fn=lambda data: data.charger_active_power_l1,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="charger_active_power_l2",
            name="Chargering Power L2",
            rm_type=Measurements,
            value_fn=lambda data: data.charger_active_power_l2,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="charger_active_power_l3",
            name="Chargering Power L3",
            rm_type=Measurements,
            value_fn=lambda data: data.charger_active_power_l3,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            suggested_unit_of_measurement=UnitOfPower.KILO_WATT,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Measurements](
            key="active_energy_import_total",
            name="Charged Energy",
            icon="mdi:ev-station",
            rm_type=Measurements,
            value_fn=lambda data: data.active_energy_import_total,
            state_class=SensorStateClass.TOTAL,
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="state_num",
            name="Mode 3 State (enum)",
            icon="mdi:ev-station",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_num.name,
            device_class=SensorDeviceClass.ENUM,
            options=[s.name for s in Mode3State],
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="state_str",
            name="Mode 3 State (name)",
            icon="mdi:ev-station",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_str,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="pwm_amp",
            name="Mode 3 PWM (Amps)",
            rm_type=Mode3Details,
            value_fn=lambda data: data.pwm_amp,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="pwm",
            name="Mode 3 PWM (%)",
            icon="mdi:percent",
            rm_type=Mode3Details,
            value_fn=lambda data: data.pwm / 10,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            suggested_display_precision=1,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="pp",
            name="Mode 3 Proximity Pilot (cable rating)",
            rm_type=Mode3Details,
            value_fn=lambda data: data.pp,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="cp_pos",
            name="Mode 3 Control Pilot +",
            rm_type=Mode3Details,
            value_fn=lambda data: data.CP_pos,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="cp_neg",
            name="Mode 3 Control Pilot -",
            rm_type=Mode3Details,
            value_fn=lambda data: data.CP_neg,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[CurrentOffered](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="active_current_offered",
            name="Active Current Offered",
            rm_type=CurrentOffered,
            value_fn=lambda data: data.active_current_offered,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
            suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=2,
        ),
    ]

    if ems_control:
        per_port.append(
            EnovatesSensorEntityDescription[TransactionToken](
                key="transaction_token",
                name="Transaction Token",
                icon="mdi:identifier",
                rm_type=TransactionToken,
                value_fn=lambda data: data.transaction_token,
            )
        )
    else:
        per_port.append(
            EnovatesSensorEntityDescription[EMSLimit](
                entity_category=EntityCategory.DIAGNOSTIC,
                key="ems_limit",
                name="EMS Limit",
                rm_type=EMSLimit,
                value_fn=lambda data: data.ems_limit,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.CURRENT,
                native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
                suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                suggested_display_precision=2,
            )
        )

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
    """Set up the sensor platform."""
    shared, per_port = _entity_descriptions(sorted(entry.runtime_data.clients.keys()), ems_control=entry.runtime_data.ems_control)

    diagnostics = await entry.runtime_data.clients[1].get_diagnostics()

    async_add_entities(
        EnovatesSensor(
            diagnostics=diagnostics,
            coordinator=entry.runtime_data.coordinator(1, ed.rm_type),
            entity_description=ed,
        )
        for ed in shared
    )

    for device_id, eds in per_port.items():
        async_add_entities(
            EnovatesSensor(
                diagnostics=diagnostics,
                coordinator=entry.runtime_data.coordinator(device_id, ed.rm_type),
                entity_description=ed,
            )
            for ed in eds
        )


class EnovatesSensor[T: RegisterMap](EnovatesEntity, SensorEntity):
    """Enovates Sensor class."""

    entity_description: EnovatesSensorEntityDescription[T]

    def __init__(
        self,
        diagnostics: Diagnostics,
        coordinator: DataUpdateCoordinator[T],
        entity_description: EnovatesSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
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
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
