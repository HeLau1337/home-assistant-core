"""Config flow for DeLonghi PAC N90 Customized AC."""

import logging
from typing import Any

import requests
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import CONF_BASE_URL, CONF_DEFAULT_BASE_URL, CONF_DEFAULT_NAME, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=CONF_DEFAULT_NAME): str,
        vol.Required(CONF_BASE_URL, default=CONF_DEFAULT_BASE_URL): str,
    }
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.

    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    base_url = data[CONF_BASE_URL]
    if len(base_url) < 10 or not base_url.startswith("http"):
        raise InvalidBaseUrl

    result = requests.get(f"{base_url}", timeout=5)
    if not result.ok:
        # If there is an error, raise an exception to notify HA that there was a
        # problem. The UI will also show there was a problem
        raise CannotConnect

    return {"title": data[CONF_NAME]}


class DeLonghiIrRemoteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a custom DeLonghi IR remote config flow."""

    VERSION = 1
    MINOR_VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidBaseUrl:
                errors[CONF_BASE_URL] = "invalid_base_url"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidBaseUrl(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid base url."""
