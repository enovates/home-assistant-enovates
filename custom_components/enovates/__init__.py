"""
Enovates EVSE Integration for Home Assistant.

Copyright 2026 Enovates NV

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from enovates_modbus.base import RegisterMap
from enovates_modbus.eno_one import (
    APIVersion,
    CurrentOffered,
    Diagnostics,
    EMSLimit,
    EnoOneClient,
    Measurements,
    Mode3Details,
    State,
    TransactionToken,
)
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.loader import async_get_loaded_integration
from pymodbus import ModbusException

from .const import CONF_DUAL_PORT, CONF_EMS_CONTROL, DOMAIN, LOGGER
from .coordinator import EnovatesDUCoordinator
from .data import EnovatesData

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from .data import EnovatesConfigEntry


PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
]

# Update in docs if changed!
REFRESH_FREQUENCY: dict[type[RegisterMap], timedelta] = {
    APIVersion: timedelta(days=1),
    Diagnostics: timedelta(days=1),
    TransactionToken: timedelta(minutes=1),
    Mode3Details: timedelta(seconds=10),
    State: timedelta(seconds=10),
    EMSLimit: timedelta(seconds=10),
    Measurements: timedelta(seconds=1),
    CurrentOffered: timedelta(seconds=1),
}


async def async_setup_entry(hass: HomeAssistant, entry: EnovatesConfigEntry) -> bool:
    """Set up Enovates config entry for Home Assistant using the UI."""

    def update_method[T: RegisterMap](device_id: int, rm_type: type[T]) -> Callable[[], Awaitable[T]]:
        # Capture the device_id and register map in the closure
        async def update() -> T:
            try:
                return await entry.runtime_data.clients[device_id].fetch(rm_type)
            except (ConnectionError, ModbusException) as e:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="update_failed",
                    translation_placeholders={
                        "port": device_id,
                        "rm_type": rm_type.__name__,
                        "e": repr(e),
                    },
                ) from e

        return update

    device_ids = (1, 2) if entry.data[CONF_DUAL_PORT] else (1,)

    ed = EnovatesData(
        ems_control=entry.data[CONF_EMS_CONTROL],
        integration=async_get_loaded_integration(hass, entry.domain),
        clients={
            i: EnoOneClient(
                host=entry.data[CONF_HOST],
                port=entry.data[CONF_PORT],
                device_id=i,
                mb_retries=3,
                mb_timeout=3,
            )
            for i in device_ids
        },
        coordinators={
            (i, rm_type): EnovatesDUCoordinator(
                hass=hass,
                logger=LOGGER,
                name=DOMAIN,
                config_entry=entry,
                update_interval=interval,
                update_method=update_method(i, rm_type),
                always_update=False,
            )
            for rm_type, interval in REFRESH_FREQUENCY.items()
            if (entry.data[CONF_EMS_CONTROL] or not issubclass(rm_type, TransactionToken))
            for i in device_ids
        },
    )
    entry.runtime_data = ed
    for c in ed.coordinators.values():
        await c.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: EnovatesConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        for client in entry.runtime_data.clients.values():
            client.client.close()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: EnovatesConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
