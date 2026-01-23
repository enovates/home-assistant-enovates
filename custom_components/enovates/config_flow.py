"""Adds config flow for Enovates."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from enovates_modbus.eno_one import EnoOneClient
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from pymodbus.exceptions import ModbusException

from .const import CONF_DUAL_PORT, CONF_EMS_CONTROL, DOMAIN, LOGGER


class EnovatesFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Enovates."""

    VERSION = 1

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        if user_input:
            client = EnoOneClient(user_input[CONF_HOST], user_input[CONF_PORT], 1, mb_timeout=1, mb_retries=10)
            try:
                await client.check_version()
            except (ConnectionError, ModbusException) as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except Exception as exception:  # noqa: BLE001
                LOGGER.exception(exception)
                errors["base"] = "unknown"
            else:
                diag = await client.get_diagnostics()
                await self.async_set_unique_id(diag.serial_nr)

                self._abort_if_unique_id_mismatch(reason="wrong_device")

                if user_input[CONF_EMS_CONTROL]:
                    try:
                        await client.get_transaction_token()
                    except (ConnectionError, ModbusException) as exception:
                        LOGGER.error(exception)
                        errors["base"] = "ems_control_disabled"
                    except Exception as exception:  # noqa: BLE001
                        LOGGER.exception(exception)
                        errors["base"] = "unknown"

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or self._get_reconfigure_entry().data).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or self._get_reconfigure_entry().data).get(CONF_PORT, 502),
                    ): cv.port,
                    vol.Required(
                        CONF_DUAL_PORT,
                        default=(user_input or self._get_reconfigure_entry().data).get(CONF_DUAL_PORT, False),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_EMS_CONTROL,
                        default=(user_input or self._get_reconfigure_entry().data).get(CONF_EMS_CONTROL, False),
                    ): selector.BooleanSelector(),
                },
            ),
            errors=errors,
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            client = EnoOneClient(user_input[CONF_HOST], user_input[CONF_PORT], 1, mb_timeout=1, mb_retries=10)
            try:
                await client.check_version()
            except (ConnectionError, ModbusException) as exception:
                LOGGER.error(exception)
                errors["base"] = "connection"
            except Exception as exception:  # noqa: BLE001
                LOGGER.exception(exception)
                errors["base"] = "unknown"
            else:
                diag = await client.get_diagnostics()
                await self.async_set_unique_id(diag.serial_nr)

                self._abort_if_unique_id_configured()

                if user_input[CONF_EMS_CONTROL]:
                    try:
                        await client.get_transaction_token()
                    except (ConnectionError, ModbusException) as exception:
                        LOGGER.error(exception)
                        errors["base"] = "ems_control_disabled"
                    except Exception as exception:  # noqa: BLE001
                        LOGGER.exception(exception)
                        errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=f"ENO one - {diag.serial_nr}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or {}).get(CONF_PORT, 502),
                    ): cv.port,
                    vol.Required(
                        CONF_DUAL_PORT,
                        default=(user_input or {}).get(CONF_DUAL_PORT, False),
                    ): selector.BooleanSelector(),
                    vol.Required(
                        CONF_EMS_CONTROL,
                        default=(user_input or {}).get(CONF_EMS_CONTROL, False),
                    ): selector.BooleanSelector(),
                },
            ),
            errors=errors,
        )
