"""Test the Simple Integration config flow."""

from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from enovates_modbus.eno_one import Diagnostics
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.enovates.const import DOMAIN


@pytest.mark.asyncio
@mock.patch("enovates_modbus.EnoOneClient", autospec=True)
async def test_flow_happy(mock_client: MagicMock, hass: HomeAssistant):
    """Test happy config flow."""
    mock_client.return_value.check_version.return_value = True
    mock_client.return_value.get_diagnostics.return_value = Diagnostics(
        manufacturer="Enovates TEST",
        vendor_id="eNovates TEST",
        serial_nr="7",
        model_id="42",
        firmware_version="3.14",
    )

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.enovates.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "127.0.0.1",
                "port": 502,
                "dual_port": False,
                "ems_control": False,
            },
        )

    mock_client.assert_called_once()
    mock_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ENO one - 7"
    assert result2["data"] == {
        "host": "127.0.0.1",
        "port": 502,
        "dual_port": False,
        "ems_control": False,
    }
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
@mock.patch("enovates_modbus.EnoOneClient", autospec=True)
async def test_flow_no_connection(mock_client: MagicMock, hass: HomeAssistant):
    """Test no connection config flow."""
    mock_client.return_value.check_version.side_effect = ConnectionError()

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "custom_components.enovates.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "127.0.0.1",
                "port": 502,
                "dual_port": False,
                "ems_control": False,
            },
        )

    mock_client.assert_called_once()
    mock_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "connection"}
