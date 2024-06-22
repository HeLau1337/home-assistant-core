"""Constants for the DeLonghi PAC N90 Customized AC integration."""

from homeassistant.components import climate

DOMAIN = "delonghi_pac_n90_customized"

HVACMode = climate.const.HVACMode

HA_TO_DELONGHI_HVAC = {
    HVACMode.COOL: "air-conditioning",
    HVACMode.DRY: "dehumidifying",
    HVACMode.FAN_ONLY: "fan",
    HVACMode.OFF: "standby",
}
FAN_LOW = "low"
FAN_MEDIUM = "medium"
FAN_HIGH = "high"

CONF_BASE_URL = "Base URL"
CONF_DEFAULT_NAME = "DeLonghi PAC N90 ECO SILENT"
CONF_DEFAULT_BASE_URL = "http://esp-ir-remote"
