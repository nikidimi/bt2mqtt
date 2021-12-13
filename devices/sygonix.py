from cometblue_lite import CometBlue
from .base_thermo import BaseThermo

pin = 0

class Sygonix(BaseThermo):
    def __init__(self, config):
        self._conn = CometBlue(config["mac"], pin)
        super().__init__(config["mac"])

    @property
    def supports_current_temp(self):
        return True

    @property
    def manufacturer(self):
        return "Sygonix"

    @property
    def model(self):
        return "HT100BT"
