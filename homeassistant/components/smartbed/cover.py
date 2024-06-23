"""Platform for sensor integration."""

from __future__ import annotations

import logging
from pprint import pformat
from typing import Any

import voluptuous as vol

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    CONF_API,
    CONF_BASE_URL,
    CONF_DEFAULT_BASE_URL,
    CONF_DEFAULT_NAME,
    CONF_MOTOR_TYPE,
)
from .esp_smartbed_api_client import EspSmartBedApiClient
from .models import SmartBedMotorState, SmartBedMotorType, SmartBedState

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=CONF_DEFAULT_NAME): cv.string,
        vol.Required(CONF_BASE_URL, default=CONF_DEFAULT_BASE_URL): cv.string,
        # vol.Required(CONF_MOTOR_TYPE): cv.enum(SmartBedMotorType),
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the cover platform."""
    _LOGGER.info(pformat(config))

    cover_h = {
        CONF_NAME: f"{config[CONF_NAME]} Head Motor",
        CONF_BASE_URL: config[CONF_BASE_URL],
        CONF_API: EspSmartBedApiClient(
            config[CONF_BASE_URL], async_get_clientsession(hass)
        ),
        CONF_MOTOR_TYPE: SmartBedMotorType.HEAD,
    }
    cover_f = cover_h.copy()
    cover_f[CONF_NAME] = f"{config[CONF_NAME]} Foot Motor"
    cover_f[CONF_MOTOR_TYPE] = SmartBedMotorType.FOOT

    add_entities([SmartBedMotor(cover_h), SmartBedMotor(cover_f)])


class SmartBedMotor(CoverEntity):
    """Representation of SmartBed motor (head or foot)."""

    _attr_device_class: CoverDeviceClass | None = CoverDeviceClass.GARAGE
    _attr_supported_features: CoverEntityFeature | None = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, cover) -> None:
        """Initialize the cover device."""
        self._name = cover[CONF_NAME]
        self._api: EspSmartBedApiClient = cover[CONF_API]
        self._motor_state: SmartBedMotorState = SmartBedMotorState(
            type=cover[CONF_MOTOR_TYPE], up="off", down="off"
        )
        self._is_closed = True
        self._opening_duration = 0  # seconds
        self._closing_duration = 0
        if self._motor_state.type == SmartBedMotorType.HEAD:
            self._fully_opened_duration = 20
            self._fully_closed_duration = 14
        elif self._motor_state.type == SmartBedMotorType.FOOT:
            self._fully_opened_duration = 14
            self._fully_closed_duration = 10

    @property
    def name(self) -> str:
        """Return the display name of this SmartBed motor."""
        return self._name

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        return self._is_closed

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing."""
        return self._motor_state.down == "on"

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening."""
        return self._motor_state.up == "on"

    async def async_update(self) -> None:
        """Fetch new state data for the cover.

        This is the only method that should fetch new data for Home Assistant.
        """
        smart_bed_state: SmartBedState | None = await self._api.async_get_status()
        if smart_bed_state:
            if self._motor_state.type == SmartBedMotorType.HEAD:
                self._motor_state.up = smart_bed_state.hu
                self._motor_state.down = smart_bed_state.hd
            elif self._motor_state.type == SmartBedMotorType.FOOT:
                self._motor_state.up = smart_bed_state.fu
                self._motor_state.down = smart_bed_state.fd

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        new_state = SmartBedMotorState(type=self._motor_state.type, up="on", down="off")
        success = await self._api.async_set_motor_state(new_state)
        if success:
            self._is_closed = False
            self._motor_state = new_state

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        new_state = SmartBedMotorState(type=self._motor_state.type, up="off", down="on")
        success = await self._api.async_set_motor_state(new_state)
        if success:
            self._motor_state = new_state

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        new_state = SmartBedMotorState(
            type=self._motor_state.type, up="off", down="off"
        )
        success = await self._api.async_set_motor_state(new_state)
        if success:
            self._motor_state = new_state
