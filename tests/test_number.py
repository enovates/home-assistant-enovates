"""Tests for number platform."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enovates.const import CONF_DUAL_PORT, CONF_EMS_CONTROL


@pytest.mark.asyncio
@patch("custom_components.enovates.PLATFORMS", [Platform.NUMBER])
@pytest.mark.parametrize(
    "entry",
    [(False, False), (False, True), (True, False), (True, True)],
    indirect=True,
    ids=lambda e: f"dual_port={e[0]},ems_control={e[1]}",
)
async def test_entities(eno_one_client: AsyncMock, entry: MockConfigEntry, hass: HomeAssistant, entity_registry: EntityRegistry):
    """Test that the correct nr of entities get registered."""
    ems = entry.data[CONF_EMS_CONTROL]
    dual = entry.data[CONF_DUAL_PORT]
    device_ids = {1, 2} if dual else {1}

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    if ems:
        assert len(entity_registry.async_device_ids()) == 1
        assert len(entity_registry.entities) == len(device_ids)
    else:
        assert len(entity_registry.async_device_ids()) == 0
        assert len(entity_registry.entities) == 0

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
