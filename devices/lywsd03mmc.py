import json
import time
from bluepy.btle import Scanner, DefaultDelegate
from bluepy import btle


class Lywsd03Mmc:
    def __init__(self, config):
        self._mac = config["mac"]
        self._last_update = 0
        self._id = self._mac.replace(":", "-")


    def get_channel_prefix(self):
        return "lywsd03mmc/" + self._id + "/"

    def get_device_description(self):
        data = {     
            "identifiers":[
                self._id,
            ],
            "manufacturer": "Xiaomi",
            "model": "Mijia LYWSD03MMC"
        }
        return data

    def get_data_temp(self):
        data = {     
            "unique_id": self._id + "-temp",
            "state_topic": self.get_channel_prefix() + "temp", 
            "name": "Temperature",
            "device_class": "temperature",
            "unit_of_measurement": "°C",
            "device": self.get_device_description()
        }
        return data
    
    def get_data_humidity(self):
        data = {     
            "unique_id": self._id + "-humidity",
            "state_topic": self.get_channel_prefix() + "humidity", 
            "name": "Humidity",
            "device_class": "humidity",
            "unit_of_measurement": "%",
            "device": self.get_device_description()
        }
        return data

    def get_data_battery(self):
        data = {     
            "unique_id": self._id + "-battery",
            "state_topic": self.get_channel_prefix() + "battery", 
            "name": "Battery",
            "device_class": "battery",
            "unit_of_measurement": "%",
            "device": self.get_device_description()
        }
        return data

    @property
    def mac(self):
        return self._mac

    def update_if_necessary(self, client):
        if self.should_update():
            class ScanDelegate(DefaultDelegate):
                def __init__(self, device):
                    DefaultDelegate.__init__(self)
                    self.ready = False
                    self._device = device
                    
                def handleDiscovery(self, dev, isNewDev, isNewData):
                    if not isNewDev:
                        if dev.addr == self._device.mac:
                            data = bytes.fromhex(dev.getValueText(22))  
                            temperature = int.from_bytes(data[8:10], byteorder='little', signed=True) * 0.01
                            humidity = int.from_bytes(data[10:12], byteorder='little', signed=False) * 0.01
                            battery = int.from_bytes(data[12:14], byteorder='little', signed=False) * 0.01

                            client.publish(self._device.get_channel_prefix() + "temp", payload="{:.2f}".format(temperature), qos=0, retain=False)
                            client.publish(self._device.get_channel_prefix() + "humidity", payload="{:.2f}".format(humidity), qos=0, retain=False)
                            client.publish(self._device.get_channel_prefix() + "battery", payload="{:.2f}".format(battery), qos=0, retain=False)

                            self.ready = True

            try:
                delegate = ScanDelegate(self)
                scanner = Scanner().withDelegate(delegate)
                scanner.clear()
                scanner.start()
                for i in range(10):
                    scanner.process(10)
                    if delegate.ready:
                        break
                scanner.stop()
            except (BrokenPipeError, btle.BTLEDisconnectError):
                pass


    def should_update(self):
        return time.time() - self._last_update > 600

    def get_id(self):
        return self._id

    def on_connect(self, client):
        client.publish("homeassistant/sensor/" + self.get_id() + "-temp/config", payload=json.dumps(self.get_data_temp()), qos=0, retain=False)
        client.publish("homeassistant/sensor/" + self.get_id() + "-humidity/config", payload=json.dumps(self.get_data_humidity()), qos=0, retain=False)
        client.publish("homeassistant/sensor/" + self.get_id() + "-battery/config", payload=json.dumps(self.get_data_battery()), qos=0, retain=False)
