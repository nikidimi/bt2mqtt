import time
import json
import sys
import serial

class Hpma115S0:
    def __init__(self, config):
        self._serial = serial.Serial('/dev/serial0')
        self._id = config["name"]
        self._last_update = 0

        # Stop autosend
        self._serial.write(bytes([0x68, 0x01, 0x20, 0x77]))
        # Stop measurement
        self._serial.write(bytes([0x68, 0x01, 0x02, 0x95]))

    def get_channel_prefix(self):
        return "airquality/" + self._id + "/"

    def get_data_pm25(self):
        data = {     
            "unique_id": self._id + "-pm25",
            "state_topic": self.get_channel_prefix() + "pm25", 
            "name": "PM 2.5",
            "device_class": "pm25",
            "unit_of_measurement": "μg/m3",
            "device":{
                "identifiers":[
                    self._id,
                ],
                "manufacturer": "Honeywell",
                "model": "HPMA115S0-XXX"
            }
        }
        return data

    
    def get_data_pm10(self):
        data = {     
            "unique_id": self._id + "-pm10",
            "state_topic": self.get_channel_prefix() + "pm10", 
            "name": "PM 10",
            "device_class": "pm10",
            "unit_of_measurement": "μg/m3",
            "device":{
                "identifiers":[
                    self._id,
                ],
            }
        }
        return data

    def update_if_necessary(self, client):
        if self.should_update():
            # Start fan for measurement
            self._serial.write(bytes([0x68, 0x01, 0x01, 0x96]))
            # Wait for spin-up 
            time.sleep(10)
            # Get measurement
            self._serial.write(bytes([0x68, 0x01, 0x04, 0x93]))
            while self._serial.read()[0] != 0x40:
                pass
            
            res = self._serial.read(7)
            if res[0] == 0x05 and res[1] == 0x04:
                pm25 = int.from_bytes(res[2:4], byteorder='big')
                pm10 = int.from_bytes(res[4:6], byteorder='big')
                checksum = res[6]
                client.publish(self.get_channel_prefix() + "pm25", payload=pm25, qos=0, retain=False)
                client.publish(self.get_channel_prefix() + "pm10", payload=pm10, qos=0, retain=False)

            # Stop fan
            self._serial.write(bytes([0x68, 0x01, 0x02, 0x95]))
            self._last_update = time.time()


    def should_update(self):
        return time.time() - self._last_update > 600

    def get_id(self):
        return self._id

    def on_connect(self, client):
        client.publish("homeassistant/sensor/" + self.get_id() + "-pm25/config", payload=json.dumps(self.get_data_pm25()), qos=0, retain=False)
        client.publish("homeassistant/sensor/" + self.get_id() + "-pm10/config", payload=json.dumps(self.get_data_pm10()), qos=0, retain=False)
