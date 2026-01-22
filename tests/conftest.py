"""Fixtures for testing."""

from unittest.mock import PropertyMock, patch

import pytest
from enovates_modbus.base import RegisterMap
from enovates_modbus.eno_one import (
    APIVersion,
    CurrentOffered,
    Diagnostics,
    EMSLimit,
    LEDColor,
    LockState,
    Measurements,
    Mode3Details,
    Mode3State,
    State,
    TransactionToken,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from pymodbus import ModbusException
from pymodbus.client import AsyncModbusTcpClient
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from custom_components.enovates.const import CONF_DUAL_PORT, CONF_EMS_CONTROL, DOMAIN


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    return


@pytest.fixture
def entry(request):
    dual_port, ems_control = request.param

    return MockConfigEntry(
        entry_id="enovates-eno-one-test-entry-id",
        domain=DOMAIN,
        title="ENO one test entry",
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 502,
            CONF_DUAL_PORT: dual_port,
            CONF_EMS_CONTROL: ems_control,
        },
    )


@pytest.fixture
def eno_one_client(entry):
    with patch("custom_components.enovates.EnoOneClient", autospec=True) as client:
        data = {
            APIVersion: APIVersion(
                major=1,
                minor=2,
            ),
            State: State(
                number_of_phases=1,
                max_amp_per_phase=16,
                ocpp_state=False,
                load_shedding_state=False,
                lock_state=LockState.NO_LOCK_PRESENT,
                contactor_state=False,
                led_color=LEDColor.RED,
            ),
            Measurements: Measurements(
                current_l1=6,
                current_l2=7,
                current_l3=8,
                voltage_l1=1,
                voltage_l2=2,
                voltage_l3=3,
                charger_active_power_total=42,
                charger_active_power_l1=11,
                charger_active_power_l2=12,
                charger_active_power_l3=13,
                installation_current_l1=0,
                installation_current_l2=0,
                installation_current_l3=0,
                active_energy_import_total=9001,
            ),
            Mode3Details: Mode3Details(
                state_num=Mode3State.A1,
                state_str="A1",
                pwm_amp=0,
                pwm=1000,
                pp=0,
                CP_pos=12,
                CP_neg=12,
            ),
            EMSLimit: EMSLimit(
                ems_limit=-1,
            ),
            TransactionToken: TransactionToken(
                transaction_token="B00FC4FE",
            ),
            CurrentOffered: CurrentOffered(
                active_current_offered=0,
            ),
            Diagnostics: Diagnostics(
                manufacturer="Enovates Pytest",
                vendor_id="eNovates Pytest",
                serial_nr="7",
                model_id="foo",
                firmware_version="bar",
            ),
        }

        def fetch[T: RegisterMap](register_map: type[T]) -> T:
            if not entry.data[CONF_EMS_CONTROL] and register_map == TransactionToken:
                raise ModbusException("[unittest] ems disabled, token read should raise exception")

            return data[register_map]

        client.return_value.fetch.side_effect = fetch
        client.return_value.get_diagnostics.return_value = data[Diagnostics]

        # For .close call during unload.
        client.return_value.client = PropertyMock(spec=AsyncModbusTcpClient)

        yield client
