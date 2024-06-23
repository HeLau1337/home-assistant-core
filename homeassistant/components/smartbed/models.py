"""Data classes for SmartBed data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

type OnOff = Literal["on", "off"]


class SmartBedMotorType(Enum):
    """Used for configuration of a SmartBed cover entity."""

    HEAD = "h"
    FOOT = "f"


@dataclass
class SmartBedMotorState:
    """Defines the state of a SmartBed."""

    type: SmartBedMotorType
    up: OnOff
    down: OnOff


@dataclass
class SmartBedState:
    """Defines the state of a SmartBed."""

    hu: OnOff
    hd: OnOff
    fu: OnOff
    fd: OnOff
