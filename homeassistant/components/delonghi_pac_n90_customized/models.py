"""The DeLonghi PACN 90 integration models."""

from dataclasses import dataclass


@dataclass
class DeLonghiPACN90Data:
    """Data for the DeLonghi PAC N90 integration."""

    name: str
    base_url: str
