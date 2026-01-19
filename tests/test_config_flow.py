"""Test the Simple Integration config flow."""

from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from enovates_modbus.eno_one import Diagnostics
from homeassistant import config_entries, setup

from custom_components.enovates.const import DOMAIN


@pytest.mark.asyncio
@mock.patch("enovates_modbus.EnoOneClient", autospec=True)
async def test_form(mock_client: MagicMock, hass):
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})

    mock_client.return_value.check_version.return_value = True
    mock_client.return_value.get_diagnostics.return_value = Diagnostics(
        manufacturer="Enovates TEST",
        vendor_id="eNovates TEST",
        serial_nr="7",
        model_id="42",
        firmware_version="3.14",
    )

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == "form"
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

    assert result2["type"] == "create_entry"
    assert result2["title"] == "ENO one - 7"
    assert result2["data"] == {
        "host": "127.0.0.1",
        "port": 502,
        "dual_port": False,
        "ems_control": False,
    }
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1
