"""Platform for sensor integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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

from .const import DOMAIN
from .entity import EnovatesEntity, transform_entity_descriptions_per_port

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

    from .data import EnovatesConfigEntry


# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


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
            translation_key="api_version",
            rm_type=APIVersion,
            value_fn=lambda data: f"{data.major}.{data.minor}",
        ),
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="max_amp_per_phase",
            translation_key="max_amp_per_phase",
            rm_type=State,
            value_fn=lambda data: data.max_amp_per_phase,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="installation_current_l1",
            translation_key="installation_current",
            translation_placeholders={"phase": "1"},
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
            translation_key="installation_current",
            translation_placeholders={"phase": "2"},
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
            translation_key="installation_current",
            translation_placeholders={"phase": "3"},
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
            translation_key="manufacturer",
            rm_type=Diagnostics,
            value_fn=lambda data: data.manufacturer,
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="vendor_id",
            translation_key="vendor_id",
            rm_type=Diagnostics,
            value_fn=lambda data: data.vendor_id,
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="serial_nr",
            translation_key="serial_nr",
            rm_type=Diagnostics,
            value_fn=lambda data: data.serial_nr,
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="model_id",
            translation_key="model_id",
            rm_type=Diagnostics,
            value_fn=lambda data: data.model_id,
        ),
        EnovatesSensorEntityDescription[Diagnostics](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="firmware_version",
            translation_key="firmware_version",
            rm_type=Diagnostics,
            value_fn=lambda data: data.firmware_version,
        ),
    ]

    per_port = [
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="number_of_phases",
            translation_key="number_of_phases",
            rm_type=State,
            value_fn=lambda data: data.number_of_phases,
        ),
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="lock_state",
            translation_key="lock_state",
            rm_type=State,
            value_fn=lambda data: data.lock_state.name.lower(),
            device_class=SensorDeviceClass.ENUM,
            options=[s.name.lower() for s in LockState],
        ),
        EnovatesSensorEntityDescription[State](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="led_color",
            translation_key="led_color",
            rm_type=State,
            value_fn=lambda data: data.led_color.name.lower(),
            device_class=SensorDeviceClass.ENUM,
            options=[s.name.lower() for s in LEDColor],
        ),
        EnovatesSensorEntityDescription[Measurements](
            entity_category=EntityCategory.DIAGNOSTIC,
            key="current_l1",
            translation_key="current",
            translation_placeholders={"phase": "1"},
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
            translation_key="current",
            translation_placeholders={"phase": "2"},
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
            translation_key="current",
            translation_placeholders={"phase": "3"},
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
            translation_key="voltage",
            translation_placeholders={"phase": "1"},
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
            translation_key="voltage",
            translation_placeholders={"phase": "2"},
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
            translation_key="voltage",
            translation_placeholders={"phase": "3"},
            rm_type=Measurements,
            value_fn=lambda data: data.voltage_l3,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Measurements](
            key="charger_active_power_total",
            translation_key="charger_active_power_total",
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
            entity_registry_enabled_default=False,  # Total is more useful.
            key="charger_active_power_l1",
            translation_key="charger_active_power",
            translation_placeholders={"phase": "1"},
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
            entity_registry_enabled_default=False,  # Total is more useful.
            key="charger_active_power_l2",
            translation_key="charger_active_power",
            translation_placeholders={"phase": "2"},
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
            entity_registry_enabled_default=False,  # Total is more useful.
            key="charger_active_power_l3",
            translation_key="charger_active_power",
            translation_placeholders={"phase": "3"},
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
            translation_key="active_energy_import_total",
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
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="state_num",
            translation_key="state_num",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_num.name.lower(),
            device_class=SensorDeviceClass.ENUM,
            options=[s.name.lower() for s in Mode3State],
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="state_str",
            translation_key="state_str",
            rm_type=Mode3Details,
            value_fn=lambda data: data.state_str,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="pwm_amp",
            translation_key="pwm_amp",
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
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="pwm",
            translation_key="pwm",
            rm_type=Mode3Details,
            value_fn=lambda data: data.pwm / 10,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=PERCENTAGE,
            suggested_display_precision=1,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="pp",
            translation_key="pp",
            rm_type=Mode3Details,
            value_fn=lambda data: data.pp,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.CURRENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="cp_pos",
            translation_key="cp_pos",
            rm_type=Mode3Details,
            value_fn=lambda data: data.CP_pos,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.VOLTAGE,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=0,
        ),
        EnovatesSensorEntityDescription[Mode3Details](
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,  # Mode 3 details are not really end-user things
            key="cp_neg",
            translation_key="cp_neg",
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
            translation_key="active_current_offered",
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
                translation_key="transaction_token",
                rm_type=TransactionToken,
                # Fallback required for icon/state translation to work/pass hassfest ci checks.
                # See also https://github.com/home-assistant/core/pull/159754#issuecomment-3787635927
                value_fn=lambda data: data.transaction_token or "n_a",
            )
        )
    else:
        per_port.append(
            EnovatesSensorEntityDescription[EMSLimit](
                entity_category=EntityCategory.DIAGNOSTIC,
                key="ems_limit",
                translation_key="ems_limit",
                rm_type=EMSLimit,
                value_fn=lambda data: data.ems_limit,
                state_class=SensorStateClass.MEASUREMENT,
                device_class=SensorDeviceClass.CURRENT,
                native_unit_of_measurement=UnitOfElectricCurrent.MILLIAMPERE,
                suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
                suggested_display_precision=2,
            )
        )

    return shared, transform_entity_descriptions_per_port(ports, per_port)


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
