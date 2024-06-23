"""Handles communication with the ESP8266 webserver API endpoint for setting the AC unit's state by sending the corresponding infrared signals."""

import logging

import aiohttp

from .const import HA_TO_DELONGHI_HVAC, HVACMode

_LOGGER = logging.getLogger(__name__)


class EspIrRemoteApiClient:
    """Handles communication with the ESP8266 webserver API endpoint for setting the AC unit's state by sending the corresponding infrared signals."""

    DELONGHI_AC_ENDPOINT = "delonghi-ac"

    def __init__(self, base_url: str, session: aiohttp.ClientSession) -> None:
        """Initialize the API by setting the base url."""
        self._base_url = base_url
        self._session = session

    async def async_test_connection(self) -> bool:
        """Test the connection to the base url."""
        async with self._session.get(f"{self._base_url}/", timeout=600) as response:
            return response.status == 200

    async def async_set_state(
        self,
        hvac_mode: HVACMode,
        fan_mode: str | None = None,
        target_temperature: float | None = None,
    ) -> aiohttp.ClientResponse:
        """Send a GET request to the API endpoint for setting a new state of the AC unit."""
        params = {}
        if hvac_mode:
            params["mode"] = HA_TO_DELONGHI_HVAC.get(hvac_mode)
        if fan_mode:
            params["fanSpeed"] = fan_mode.lower()
        if target_temperature:
            params["temperature"] = str(int(target_temperature))

        async with self._session.get(
            f"{self._base_url}/{self.DELONGHI_AC_ENDPOINT}", params=params, timeout=600
        ) as response:
            # _LOGGER.debug(
            #    "Sent GET request: %s",
            #    response.url,
            # )
            if response.status == 200:
                _LOGGER.debug(
                    "Response status code: %s | Response text: %s",
                    response.status,
                    await response.text(),
                )
            else:
                _LOGGER.error(
                    "Response status code: %s | Response text: %s",
                    response.status,
                    await response.text(),
                )
            return response
