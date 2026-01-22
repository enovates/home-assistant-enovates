"""Tests for binary_sensor platform."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enovates.const import CONF_DUAL_PORT


@pytest.mark.asyncio
@patch("custom_components.enovates.PLATFORMS", [Platform.BINARY_SENSOR])
@pytest.mark.parametrize(
    "entry",
    [(False, False), (False, True), (True, False), (True, True)],
    indirect=True,
    ids=lambda e: f"dual_port={e[0]},ems_control={e[1]}",
)
async def test_entities(eno_one_client: AsyncMock, entry: MockConfigEntry, hass: HomeAssistant, entity_registry: EntityRegistry):
    """Test that the correct nr of entities get registered."""
    dual = entry.data[CONF_DUAL_PORT]
    device_ids = {1, 2} if dual else {1}

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(entity_registry.async_device_ids()) == 1
    assert len(entity_registry.entities) == len(device_ids) * 6 + 2

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
