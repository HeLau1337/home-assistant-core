"""Handles communication with the ESP8266 webserver API endpoint for setting the SmartBed's state."""

import json
import logging

import aiohttp

from .models import SmartBedMotorState, SmartBedState

_LOGGER = logging.getLogger(__name__)


class EspSmartBedApiClient:
    """Handles communication with the ESP8266 webserver API endpoint for setting the SmartBed's state."""

    SET_STATE_ENDPOINT = "set"
    STATUS_ENDPOINT = "status"

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API by setting the base url."""
        self._base_url = base_url
        self._session = session

    async def async_test_connection(self) -> bool:
        """Test the connection to the base url."""
        async with self._session.get(f"{self._base_url}/", timeout=600) as response:
            return response.status == 200

    async def async_set_motor_state(self, motor: SmartBedMotorState) -> bool | None:
        """Send a GET request to the API endpoint for setting a new state of the SmartBed."""
        params = {
            f"{motor.type.value}u": motor.up,
            f"{motor.type.value}d": motor.down,
        }

        async with self._session.get(
            f"{self._base_url}/{self.SET_STATE_ENDPOINT}", params=params, timeout=600
        ) as response:
            return response.status == 200

    async def async_get_status(self) -> SmartBedState | None:
        """Get the current state of the SmartBed."""
        async with self._session.get(
            f"{self._base_url}/{self.STATUS_ENDPOINT}", timeout=600
        ) as response:
            text = await response.text()
            return self._handle_response(response, text)

    def _handle_response(
        self, response: aiohttp.ClientResponse, text: str
    ) -> SmartBedState | None:
        if response.status == 200:
            _LOGGER.debug(
                "Response status code: %s | Response text: %s",
                response.status,
                text,
            )
            resp_json = json.loads(text)
            return SmartBedState(**resp_json)

        _LOGGER.error(
            "Response status code: %s | Response text: %s",
            response.status,
            text,
        )
        return None
