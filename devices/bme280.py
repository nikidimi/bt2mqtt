import bme280
import smbus2
import json
import time

class Bme280:
    def __init__(self, config):
        port = 1
        self._address = 0x76
        self._bus = smbus2.SMBus(port)
        self._id = config["name"]
        self._last_update = 0

        bme280.load_calibration_params(self._bus, self._address)


    def get_channel_prefix(self):
        return "bme280/" + self._id + "/"

    def get_device_description(self):
        data = {     
            "identifiers":[
                self._id,
            ],
            "manufacturer": "Bosch",
            "model": "BME280"
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

    def get_data_pressure(self):
        data = {     
            "unique_id": self._id + "-pressure",
            "state_topic": self.get_channel_prefix() + "pressure", 
            "name": "Pressure",
            "device_class": "pressure",
            "unit_of_measurement": "hPa",
            "device": self.get_device_description()
        }
        return data

    def update_if_necessary(self, client):
        if self.should_update():
            bme280_data = bme280.sample(self._bus, self._address)
            client.publish(self.get_channel_prefix() + "temp", payload="{:.2f}".format(bme280_data.temperature), qos=0, retain=False)
            client.publish(self.get_channel_prefix() + "humidity", payload="{:.2f}".format(bme280_data.humidity), qos=0, retain=False)
            client.publish(self.get_channel_prefix() + "pressure", payload="{:.2f}".format(bme280_data.pressure), qos=0, retain=False)


    def should_update(self):
        return time.time() - self._last_update > 600

    def get_id(self):
        return self._id

    def on_connect(self, client):
        client.publish("homeassistant/sensor/" + self.get_id() + "-temp/config", payload=json.dumps(self.get_data_temp()), qos=0, retain=False)
        client.publish("homeassistant/sensor/" + self.get_id() + "-humidity/config", payload=json.dumps(self.get_data_humidity()), qos=0, retain=False)
        client.publish("homeassistant/sensor/" + self.get_id() + "-pressure/config", payload=json.dumps(self.get_data_pressure()), qos=0, retain=False)
