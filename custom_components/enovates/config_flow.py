"""Config flow for the enovates integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, LOGGER
from enovates_modbus.modbusenoone import ModbusEnoOne

_LOGGER = logging.getLogger(__name__)

# Step 1: Initial connection data
STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})

# Step 2: Loadshedding device question
STEP_LOADSHEDDING_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("has_loadshedding_device", default=False): bool,
    }
)


def create_api(hostname) -> ModbusEnoOne | None:
    """Create an instance of the api."""
    LOGGER.warning("Creating Enovates Modbus API to: " + hostname)
    try:
        return ModbusEnoOne(hostname)
    except:
        return None


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = await hass.async_add_executor_job(create_api, data[CONF_HOST])
    if api is None:
        raise CannotConnect
    LOGGER.info("Successfully connected to {}", data[CONF_HOST])
    return {
        "device_serial": api.get_serial(),
        "host": data[CONF_HOST],
        "model_number": api.get_model_number(),
        "has_lock": api.get_lock_state() != 2,
    }


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for enovates."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._validated_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                validated_input = await validate_input(self.hass, user_input)
                # Store the validated input for the next step
                self._validated_input = validated_input
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check for existing config entry
                await self.async_set_unique_id(validated_input["device_serial"])
                self._abort_if_unique_id_configured()

                # Move to the loadshedding device question
                return await self.async_step_loadshedding()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_loadshedding(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the loadshedding device configuration step."""
        if user_input is not None:
            # Ensure we have validated input
            if not self._validated_input:
                _LOGGER.error("No validated input available in loadshedding step")
                return self.async_abort(reason="missing_validated_input")

            # Combine the validated input with the loadshedding device info
            final_data = {
                **self._validated_input,
                "has_loadshedding_device": user_input["has_loadshedding_device"],
                "has_ems_enabled": True,  # TODO make this variable
            }

            # Get the title, with a fallback if device_serial is not available
            title = self._validated_input.get("device_serial", "Enovates Device")

            _LOGGER.info(
                "Creating config entry with title: %s, data: %s", title, final_data
            )

            return self.async_create_entry(title=title, data=final_data)

        return self.async_show_form(
            step_id="loadshedding",
            data_schema=STEP_LOADSHEDDING_DATA_SCHEMA,
            description_placeholders={
                "device_serial": self._validated_input.get("device_serial", "Unknown"),
                "model_number": self._validated_input.get("model_number", "Unknown"),
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
