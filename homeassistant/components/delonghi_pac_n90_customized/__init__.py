"""The DeLonghi PAC N90 Customized AC integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_BASE_URL
from .models import DeLonghiPACN90Data

PLATFORMS: list[Platform] = [Platform.CLIMATE]

type DeLonghiPACN90ConfigEntry = ConfigEntry[DeLonghiPACN90Data]


async def async_setup_entry(
    hass: HomeAssistant, entry: DeLonghiPACN90ConfigEntry
) -> bool:
    """Set up DeLonghi PAC N90 Customized AC from a config entry."""
    base_url = entry.data[CONF_BASE_URL]
    name = entry.data[CONF_NAME]

    entry.runtime_data = DeLonghiPACN90Data(name, base_url)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DeLonghiPACN90ConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
