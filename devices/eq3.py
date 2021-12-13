from eq3bt import Thermostat
from .base_thermo import BaseThermo


class Eq3(BaseThermo):
    def __init__(self, config):
        self._conn = Thermostat(config["mac"])
        super().__init__(config["mac"])

    @property
    def supports_current_temp(self):
        return False

    @property
    def manufacturer(self):
        return "Eqiva"

    @property
    def model(self):
        return "eQ-3"
