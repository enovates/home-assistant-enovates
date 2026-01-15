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
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_loaded_integration

from .const import DOMAIN, LOGGER
from .data import EnovatesData

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from homeassistant.core import HomeAssistant

    from .data import EnovatesConfigEntry


PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    # Platform.SWITCH,
]

REFRESH_FREQUENCY: dict[type[RegisterMap], timedelta] = {
    APIVersion: timedelta(days=1),
    Diagnostics: timedelta(days=1),
    TransactionToken: timedelta(minutes=1),
    Mode3Details: timedelta(seconds=10),
    State: timedelta(seconds=10),
    Measurements: timedelta(seconds=1),
    CurrentOffered: timedelta(seconds=1),
    EMSLimit: timedelta(seconds=1),
}


def update_method[T: RegisterMap](entry: EnovatesConfigEntry, rm_type: type[T]) -> Callable[[], Awaitable[T]]:
    """Update the coordinator."""

    async def update() -> T:
        return await entry.runtime_data.client.fetch(rm_type)

    return update


async def async_setup_entry(hass: HomeAssistant, entry: EnovatesConfigEntry) -> bool:
    """Set up Enovates config entry for Home Assistant using the UI."""
    coordinators = {
        rm_type: DataUpdateCoordinator(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=interval,
            update_method=update_method(entry, rm_type),
        )
        for rm_type, interval in REFRESH_FREQUENCY.items()
    }

    entry.runtime_data = EnovatesData(
        client=EnoOneClient(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            device_id=entry.data[CONF_DEVICE_ID],
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinators=coordinators,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    for c in coordinators.values():
        await c.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: EnovatesConfigEntry) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: EnovatesConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
