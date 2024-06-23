"""Platform for sensor integration."""

from __future__ import annotations

import logging
from pprint import pformat
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    PLATFORM_SCHEMA,
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_API,
    CONF_BASE_URL,
    CONF_DEFAULT_BASE_URL,
    CONF_DEFAULT_NAME,
    DOMAIN,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVACMode,
)
from .esp_ir_remote_api_client import EspIrRemoteApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=CONF_DEFAULT_NAME): cv.string,
        vol.Required(CONF_BASE_URL, default=CONF_DEFAULT_BASE_URL): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the climate platform."""
    _LOGGER.info(pformat(config))

    climate = {
        CONF_NAME: config[CONF_NAME],
        CONF_BASE_URL: config[CONF_BASE_URL],
        CONF_API: EspIrRemoteApiClient(
            config[CONF_BASE_URL], async_get_clientsession(hass)
        ),
    }
    add_entities([DeLonghiPACN90(climate)])


class DeLonghiPACN90(ClimateEntity):
    """Representation of a DeLonghi PAC N90 ECO SILENT air conditioning unit."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_fan_modes: list[str] = [FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_hvac_modes: list[HVACMode] = [
        HVACMode.COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
        HVACMode.OFF,
    ]
    _attr_supported_features = (
        ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, climate) -> None:
        """Initialize the climate device."""
        self._name = climate[CONF_NAME]
        self._api: EspIrRemoteApiClient = climate[CONF_API]
        self._fan_mode = FAN_LOW
        self._hvac_mode: HVACMode = HVACMode.OFF
        self._target_temperature = 24.0
        self._last_state_before_turn_off = self

    @property
    def device_info(self) -> DeviceInfo:
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._roller.roller_id)},
            # If desired, the name for the device could be different to the entity
            "name": self._name,
            "sw_version": "1.0",
            "model": "PAC N90 ECO SILENT (custom)",
            "manufacturer": "DeLonghi",
        }

    @property
    def name(self) -> str:
        """Return the display name of this DeLonghi AC unit."""
        return self._name

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode [Low, Medium, High]."""
        return self._fan_mode

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current fan mode [COOL, DRY, FAN_ONLY, OFF]."""
        return self._hvac_mode

    @property
    def target_temperature(self) -> float:
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return 1.0

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 16.0

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 32.0

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        response = await self._api.async_set_state(
            self._last_state_before_turn_off.hvac_mode,
            self._last_state_before_turn_off.fan_mode,
            self._last_state_before_turn_off.target_temperature,
        )
        if response.status == 200:
            self._hvac_mode = self._last_state_before_turn_off.hvac_mode
            self._fan_mode = self._last_state_before_turn_off.fan_mode
            self._target_temperature = (
                self._last_state_before_turn_off.target_temperature
            )
        else:
            _LOGGER.error("Failed to turn the device on!")

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        self._last_state_before_turn_off = self
        response = await self._api.async_set_state(
            HVACMode.OFF,
            self._fan_mode,
            self._target_temperature,
        )
        if response.status == 200:
            self._hvac_mode = HVACMode.OFF
        else:
            _LOGGER.error("Failed to turn the device off!")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        _LOGGER.debug("set_hvac_mode: %s -> %s", self._hvac_mode, hvac_mode)
        response = await self._api.async_set_state(
            hvac_mode, self._fan_mode, self._target_temperature
        )
        if response.status == 200:
            self._hvac_mode = hvac_mode
        else:
            _LOGGER.error(
                "Attempt to set a new HVAC mode failed! (%s -> %s)",
                self._hvac_mode,
                hvac_mode,
            )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.debug("set_fan_mode: %s -> %s", self._fan_mode, fan_mode)
        response = await self._api.async_set_state(
            self._hvac_mode, fan_mode, self._target_temperature
        )
        if response.status == 200:
            self._fan_mode = fan_mode
        else:
            _LOGGER.error(
                "Attempt to set a new fan mode failed! (%s -> %s)",
                self._fan_mode,
                fan_mode,
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (new_target_temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        _LOGGER.debug(
            "set_temperature: %s -> %s",
            self._target_temperature,
            new_target_temperature,
        )
        response = await self._api.async_set_state(
            self._hvac_mode, self._fan_mode, new_target_temperature
        )
        if response.status == 200:
            self._target_temperature = new_target_temperature
        else:
            _LOGGER.error(
                "Attempt to set a new fan mode failed! (%s -> %s)",
                self._target_temperature,
                new_target_temperature,
            )
