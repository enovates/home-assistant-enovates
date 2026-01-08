from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from enovates_modbus.modbusenoone import ModbusEnoOne


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EV charger number entities."""
    # Get your modbus coordinator/hub from the config entry
    api = config_entry.runtime_data["api"]

    entities = [EVChargerCurrentLimit(api)]

    async_add_entities(entities)


class EVChargerCurrentLimit(NumberEntity):
    """Representation of EV Charger Current Limit control."""

    def __init__(self, api: ModbusEnoOne) -> None:
        """Initialize the current limit entity."""
        self._api = api
        serial = api.get_serial()  # TODO: this should be gotton from config_entry
        self._attr_unique_id = "test_current_limit"
        self._attr_name = "EMS applied current Limit"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.MILLIAMPERE
        self._attr_mode = NumberMode.BOX  # or NumberMode.SLIDER

        # Set the range for current limit (adjust based on your charger specs)
        self._attr_native_min_value = 6000  # Minimum charging current
        self._attr_native_max_value = 32000  # Maximum charging current
        self._attr_native_step = 100  # Step size

        # Icon for the entity
        self._attr_icon = "mdi:current-ac"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="Enovates",
            name=serial,
            sw_version=api.get_firmware_version(),
            model=api.get_model_number(),
        )

    @property
    def native_value(self) -> float | None:
        """Return the current limit value."""
        try:
            # Read current limit from modbus
            # Adjust register address and scaling based on your device
            current_limit = self._api.get_ems_applied_softlimit()
            return current_limit
            # if current_limit and len(current_limit) > 0:
            #     # Apply any scaling factor if needed
            #     return float(current_limit[0])  # Adjust scaling as needed
            # return None
        except Exception as e:
            LOGGER.error(f"Error reading current limit: {e}")
            return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the current limit."""
        try:
            # Convert to integer if your device expects integer values
            scaled_value = int(value)  # Adjust scaling as needed

            # Write to modbus register
            # success = await self._api.em(
            #     address=1000,  # Replace with actual register address
            #     value=scaled_value,
            # )
            self._api.set_ems_applied_softlimit(int(value))
            success = True

            if success:
                LOGGER.info(f"Successfully set current limit to {value}A")
                # Update the entity state
                self.async_write_ha_state()
            else:
                LOGGER.error(f"Failed to set current limit to {value}A")

        except Exception as e:
            LOGGER.error(f"Error setting current limit: {e}")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return True
        # return self._coordinator.is_connected


# # Alternative implementation using a different approach for modbus communication
# class EVChargerCurrentLimitAlternative(NumberEntity):
#     """Alternative implementation with direct modbus calls."""

#     def __init__(self, modbus_hub, device_info):
#         """Initialize with modbus hub directly."""
#         self._modbus_hub = modbus_hub
#         self._device_info = device_info
#         self._attr_unique_id = f"{device_info['name']}_current_limit"
#         self._attr_name = "Current Limit"
#         self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
#         self._attr_mode = NumberMode.BOX
#         self._attr_native_min_value = 6.0
#         self._attr_native_max_value = 32.0
#         self._attr_native_step = 1.0
#         self._attr_icon = "mdi:current-ac"

#         # Modbus configuration
#         self._register_address = 1000  # Adjust for your device
#         self._slave_id = 1  # Adjust for your device

#     @property
#     def native_value(self) -> float | None:
#         """Return the current limit value."""
#         try:
#             result = self._modbus_hub.read_holding_registers(
#                 slave=self._slave_id, address=self._register_address, count=1
#             )
#             if result.isError():
#                 _LOGGER.error(f"Error reading current limit: {result}")
#                 return None

#             # Apply scaling if needed (e.g., if register stores value * 10)
#             return float(result.registers[0]) / 10.0

#         except Exception as e:
#             _LOGGER.error(f"Exception reading current limit: {e}")
#             return None

#     async def async_set_native_value(self, value: float) -> None:
#         """Set the current limit."""
#         try:
#             # Apply scaling if needed (e.g., if register expects value * 10)
#             scaled_value = int(value * 10)

#             result = await self._modbus_hub.async_write_register(
#                 slave=self._slave_id, address=self._register_address, value=scaled_value
#             )

#             if result.isError():
#                 _LOGGER.error(f"Error setting current limit: {result}")
#             else:
#                 _LOGGER.info(f"Current limit set to {value}A")
#                 self.async_write_ha_state()

#         except Exception as e:
#             _LOGGER.error(f"Exception setting current limit: {e}")
