"""Test the Simple Integration config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from enovates_modbus.eno_one import Diagnostics, TransactionToken
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pymodbus import ModbusException
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.enovates.const import DOMAIN


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_happy(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test happy config flow."""
    eno_one_client.return_value.check_version.return_value = True
    eno_one_client.return_value.get_diagnostics.return_value = Diagnostics(
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

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

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
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_no_connection(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test no connection config flow."""
    eno_one_client.return_value.check_version.side_effect = ConnectionError()

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
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

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "connection"}

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_modbus_error(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test modbus error on connect config flow."""
    eno_one_client.return_value.check_version.side_effect = ModbusException("unit test exception")

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
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

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "connection"}

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_general_error(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test general exception on connect config flow."""
    eno_one_client.return_value.check_version.side_effect = Exception()

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
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

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_ems_control_happy(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test config flow with EMS control."""
    eno_one_client.return_value.check_version.return_value = True
    eno_one_client.return_value.get_diagnostics.return_value = Diagnostics(
        manufacturer="Enovates TEST",
        vendor_id="eNovates TEST",
        serial_nr="7",
        model_id="42",
        firmware_version="3.14",
    )
    eno_one_client.return_value.get_transaction_token.return_value = TransactionToken(transaction_token="TEST")

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
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
                "ems_control": True,
            },
        )

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ENO one - 7"
    assert result2["data"] == {
        "host": "127.0.0.1",
        "port": 502,
        "dual_port": False,
        "ems_control": True,
    }
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_ems_control_wrong_device_setting(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test config flow with EMS on device set to monitoring only."""
    eno_one_client.return_value.check_version.return_value = True
    eno_one_client.return_value.get_diagnostics.return_value = Diagnostics(
        manufacturer="Enovates TEST",
        vendor_id="eNovates TEST",
        serial_nr="7",
        model_id="42",
        firmware_version="3.14",
    )
    eno_one_client.return_value.get_transaction_token.side_effect = ModbusException("unittest - read error emulator")

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
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
                "ems_control": True,
            },
        )

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "ems_control_disabled"}

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_flow_ems_control_general_error(eno_one_client: AsyncMock, hass: HomeAssistant):
    """Test config flow with token readout generic exception."""
    eno_one_client.return_value.check_version.return_value = True
    eno_one_client.return_value.get_diagnostics.return_value = Diagnostics(
        manufacturer="Enovates TEST",
        vendor_id="eNovates TEST",
        serial_nr="7",
        model_id="42",
        firmware_version="3.14",
    )
    eno_one_client.return_value.get_transaction_token.side_effect = Exception()

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
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
                "ems_control": True,
            },
        )

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}

    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0


@pytest.mark.asyncio
@patch("custom_components.enovates.config_flow.EnoOneClient", autospec=True)
async def test_duplicate_entry(eno_one_client: AsyncMock, hass: HomeAssistant) -> None:
    """Test duplicate setup handling."""
    MockConfigEntry(
        domain=DOMAIN,
        title="ENO one - 7",
        data={
            "host": "127.0.0.1",
            "port": 502,
            "dual_port": False,
            "ems_control": False,
        },
        unique_id="7",
    ).add_to_hass(hass)

    eno_one_client.return_value.check_version.return_value = True
    eno_one_client.return_value.get_diagnostics.return_value = Diagnostics(
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

    eno_one_client.assert_called_once()
    eno_one_client.return_value.check_version.assert_called_once()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 0
