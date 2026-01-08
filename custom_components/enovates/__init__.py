"""The enovatess integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from enovates_modbus.modbusenoone import ModbusEnoOne

PLATFORMS: list[str] = ["binary_sensor", "sensor", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up enovates from a config entry."""

    # Store data for your integration
    hass.data.setdefault("enovates", {})
    hass.data["enovates"][entry.entry_id] = {}
    entry.runtime_data = {}
    entry.runtime_data["api"] = ModbusEnoOne(entry.data[CONF_HOST])

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data["enovates"].pop(entry.entry_id)

    return unload_ok
