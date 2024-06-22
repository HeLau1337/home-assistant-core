"""Platform for sensor integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DeLonghiPACN90ConfigEntry
from .const import CONF_BASE_URL, DOMAIN, FAN_HIGH, FAN_LOW, FAN_MEDIUM, HVACMode
from .esp_ir_remote_api import EspIrRemoteApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DeLonghiPACN90ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up AdvantageAir climate platform."""

    instance = config_entry.runtime_data

    entities: list[ClimateEntity] = []
    entities.append(DeLonghiPACN90(instance.name, instance.base_url))
    async_add_entities(entities)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the climate platform."""
    name = hass.data[DOMAIN][CONF_NAME]
    base_url = hass.data[DOMAIN][CONF_BASE_URL]
    add_entities([DeLonghiPACN90(name, base_url)])


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

    def __init__(self, name, base_url) -> None:
        """Initialize the climate device."""
        self._name = name
        self._fan_mode = FAN_LOW
        self._hvac_mode = HVACMode.FAN_ONLY
        self._target_temperature = 24.0
        self._api = EspIrRemoteApi(base_url)
        self._last_state_before_turn_off = self

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

    def turn_on(self) -> None:
        """Turn the entity on."""
        response = self._api.send_new_state_request(
            self._last_state_before_turn_off.hvac_mode,
            self._last_state_before_turn_off.fan_mode,
            self._last_state_before_turn_off.target_temperature,
        )
        if response.ok:
            self._hvac_mode = self._last_state_before_turn_off.hvac_mode
            self._fan_mode = self._last_state_before_turn_off.fan_mode
            self._target_temperature = (
                self._last_state_before_turn_off.target_temperature
            )
        else:
            _LOGGER.error("Failed to turn the device on!")

    def turn_off(self) -> None:
        """Turn the entity off."""
        self._last_state_before_turn_off = self
        response = self._api.send_new_state_request(
            HVACMode.OFF,
            self._fan_mode,
            self._target_temperature,
        )
        if response.ok:
            self._hvac_mode = HVACMode.OFF
        else:
            _LOGGER.error("Failed to turn the device off!")

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new operation mode."""
        _LOGGER.debug("set_hvac_mode: %s -> %s", self._hvac_mode, hvac_mode)
        response = self._api.send_new_state_request(
            hvac_mode, self._fan_mode, self._target_temperature
        )
        if response.ok:
            self._hvac_mode = hvac_mode
        else:
            _LOGGER.error(
                "Attempt to set a new HVAC mode failed! (%s -> %s)",
                self._hvac_mode,
                hvac_mode,
            )

    def set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        _LOGGER.debug("set_fan_mode: %s -> %s", self._fan_mode, fan_mode)
        response = self._api.send_new_state_request(
            self._hvac_mode, fan_mode, self._target_temperature
        )
        if response.ok:
            self._fan_mode = fan_mode
        else:
            _LOGGER.error(
                "Attempt to set a new fan mode failed! (%s -> %s)",
                self._fan_mode,
                fan_mode,
            )

    def set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (new_target_temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        _LOGGER.debug(
            "set_temperature: %s -> %s",
            self._target_temperature,
            new_target_temperature,
        )
        response = self._api.send_new_state_request(
            self._hvac_mode, self._fan_mode, new_target_temperature
        )
        if response.ok:
            self._target_temperature = new_target_temperature
        else:
            _LOGGER.error(
                "Attempt to set a new fan mode failed! (%s -> %s)",
                self._target_temperature,
                new_target_temperature,
            )
