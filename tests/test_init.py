"""Tests for integration init."""

from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
from enovates_modbus.eno_one import (
    APIVersion,
    EnoOneClient,
    TransactionToken,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enovates.const import CONF_DUAL_PORT, CONF_EMS_CONTROL
from custom_components.enovates.coordinator import EnovatesDUCoordinator
from custom_components.enovates.data import EnovatesData


@pytest.mark.asyncio
@patch("custom_components.enovates.EnoOneClient", autospec=True)
@pytest.mark.parametrize("entry", [(False, False)], indirect=True, ids=lambda e: f"dual_port={e[0]},ems_control={e[1]}")
async def test_coordinator_exception(eno_one_client: AsyncMock, entry: MockConfigEntry, hass: HomeAssistant):
    """Test that the coordinator transforms Modbus exceptions to UpdateFailed for HA handling."""
    with (
        patch.object(hass.config_entries, "async_forward_entry_setups"),
        patch.object(hass.config_entries.flow, "async_init"),
    ):
        eno_one_client.return_value.fetch.side_effect = ModbusException("[unittest] modbus exception test")
        # For .close call during unload.
        eno_one_client.return_value.client = PropertyMock(spec=AsyncModbusTcpClient)

        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # The setup must have call async_config_entry_first_refresh, which will get the side effect triggered.

        c = entry.runtime_data.coordinator(1, APIVersion)
        assert isinstance(c.last_exception, UpdateFailed)
        assert isinstance(c.last_exception.__cause__, ModbusException)

        eno_one_client.return_value.fetch.assert_called()

        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "entry",
    [(False, False), (False, True), (True, False), (True, True)],
    indirect=True,
    ids=lambda e: f"dual_port={e[0]},ems_control={e[1]}",
)
async def test_init_happy(eno_one_client: AsyncMock, entry: MockConfigEntry, hass: HomeAssistant):
    """Test that the integration setup properly initializes the runtime data (clients, coordinators) and closes on unload."""
    ems = entry.data[CONF_EMS_CONTROL]
    dual = entry.data[CONF_DUAL_PORT]

    device_ids = {1, 2} if dual else {1}

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups"),
        patch.object(hass.config_entries.flow, "async_init"),
    ):
        entry.add_to_hass(hass)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert len(eno_one_client.call_args_list) == len(device_ids), "Only a single client should be setup per device id"
    assert {call.kwargs["device_id"] for call in eno_one_client.call_args_list} == device_ids, "client setup should have been called"
    for call in eno_one_client.call_args_list:
        assert call.kwargs["host"] == entry.data[CONF_HOST]
        assert call.kwargs["port"] == entry.data[CONF_PORT]

    ed = entry.runtime_data
    assert isinstance(ed, EnovatesData), "wrong data type"
    assert ed.clients.keys() == device_ids, "dual/single port config should match nr of client instances"
    assert ed.ems_control == ems, "ems control data doesn't match config data"

    register_maps = set(EnoOneClient.REGISTER_MAPS)
    if not ems:
        register_maps.remove(TransactionToken)

    for device_id in device_ids:
        for register_map in register_maps:
            c = ed.coordinator(device_id, register_map)
            assert isinstance(c, EnovatesDUCoordinator), "wrong coordinator type"

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert len(eno_one_client.return_value.client.close.call_args_list) == len(device_ids), (
        "client stop should have been called for every device id"
    )
