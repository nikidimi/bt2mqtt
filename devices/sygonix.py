from cometblue_lite import CometBlue
from .base_thermo import BaseThermo

pin = 0

class SygonixThermo(BaseThermo):
    def __init__(self, mac):
        self._conn = CometBlue(mac, pin)
        super().__init__(mac)

    @property
    def supports_current_temp(self):
        return True

    @property
    def manufacturer(self):
        return "Sygonix"

    @property
    def model(self):
        return "HT100BT"
