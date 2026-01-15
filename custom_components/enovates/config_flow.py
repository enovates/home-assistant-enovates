"""Adds config flow for Enovates."""

from __future__ import annotations

import voluptuous as vol
from enovates_modbus import EnoOneClient
from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID, CONF_HOST, CONF_PORT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from pymodbus.exceptions import ModbusException

from .const import DOMAIN, LOGGER


class EnovatesFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Enovates."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            client = EnoOneClient(user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_DEVICE_ID])
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
                return self.async_create_entry(
                    title=diag.serial_nr,
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
                        CONF_DEVICE_ID,
                        default=(user_input or {}).get(CONF_DEVICE_ID, 1),
                        description="Only relevant for EVSEs with more than 1 socket or cable.",
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=2)),
                },
            ),
            errors=errors,
        )
