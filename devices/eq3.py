from eq3bt import Thermostat
from .base_thermo import BaseThermo


class Eq3Thermo(BaseThermo):
    def __init__(self, mac):
        self._conn = Thermostat(mac)
        super().__init__(mac)

    @property
    def supports_current_temp(self):
        return False

    @property
    def manufacturer(self):
        return "Eqiva"

    @property
    def model(self):
        return "eQ-3"
