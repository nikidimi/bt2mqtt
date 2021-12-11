import paho.mqtt.client as mqtt
import json
import time
from cometblue_lite import CometBlue
from eq3bt import Thermostat
from bluepy import btle
from threading import Lock
import logging
import time
import yaml

logging.basicConfig(level=logging.DEBUG)
pin = 0

class Thermo:
    def __init__(self, mac):
        self._mac = mac
        self._id = self._mac.replace(":", "-")
        self._last_update = 0
        self._target_temp = None
        self._target_temp_lock = Lock()

        self._current_mode = None
        self._current_temp = None
        self._current_target_temp = None

    def get_channel_prefix(self):
        return "thermostat/" + self._id + "/"

    def get_data(self):
        data = {
            "unique_id": self._id,
            "min_temp": 5.0,
            "max_temp": 29.5,
            "temp_step": 0.5,
            "name": self._id,
            "qos": 1,
            "modes":[
                "heat",
                "auto",
                "off"
            ],

        "temperature_state_topic": self.get_channel_prefix() + "target_temp",
        "temperature_command_topic": self.get_channel_prefix() +  "target_temp/set",
        "mode_state_topic": self.get_channel_prefix() + "mode",
        "mode_command_topic": self.get_channel_prefix() +  "mode/set",
        "json_attributes_topic": self.get_channel_prefix() + "json_attributes",
        "current_temperature_topic": self.get_channel_prefix() +  "current_temp",

        "device":{
            "identifiers":[
                    self._id,
                ],
                "manufacturer": self.manufacturer,
                "model": self.model
            }
        }

        return data

    def update(self):
        self._current_mode = None
        self._current_temp = None
        self._current_target_temp = None

        with self._target_temp_lock:
            if self._target_temp is not None:
                self._conn.target_temperature  = self._target_temp
        try:
            self._conn.update()
        except (BrokenPipeError, btle.BTLEDisconnectError):
            pass
        else:
            self._current_mode = "heat"
            if self.supports_current_temp:
                self._current_temp = self._conn.current_temperature
            self._current_target_temp = self._conn.target_temperature


            self._last_update = time.time()
            with self._target_temp_lock:
                self._target_temp = None


    def should_update(self):
        return time.time() - self._last_update > 600 or self._target_temp is not None

    @property
    def current_temp(self):
        return self._current_temp

    @property
    def target_temp(self):
        return self._current_target_temp

    @property
    def mode(self):
        return self._current_mode

    @target_temp.setter
    def target_temp(self, temp):
        with self._target_temp_lock:
            self._target_temp = temp

    def get_id(self):
        return self._id


class Eq3Thermo(Thermo):
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

class SygonixThermo(Thermo):
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

def on_connect(client, userdata, flags, rc):
    for thermostat in userdata:
        client.subscribe(thermostat.get_channel_prefix() + "target_temp/set")

def on_message(client, userdata, msg):
    for thermostat in userdata:
        if msg.topic == thermostat.get_channel_prefix() + "target_temp/set":
            thermostat.target_temp = float(msg.payload)

    print(msg.topic+" "+str(msg.payload))

def create_thermo(device):
    if device["type"] == "eq3":
        return Eq3Thermo(device["mac"])
    elif device["type"] == "sygonix":
        return SygonixThermo(device["mac"])

if __name__ == '__main__':
    stream = open("config.yaml", 'r')
    config = yaml.safe_load(stream)

    thermostats = [create_thermo(device) for device in config["devices"]]

    client = mqtt.Client(userdata=thermostats)
    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(username=config["mqtt"]["username"], password=config["mqtt"]["password"])

    client.connect(config["mqtt"]["host"], 1883, 60)

    for thermostat in thermostats:
        client.publish("homeassistant/climate/" + thermostat.get_id() + "/thermo-test-ht100/config", payload=json.dumps(thermostat.get_data()), qos=0, retain=False)
    client.publish("lwt_topic", payload="online", qos=0, retain=False)

    client.loop_start()

    while True:
        for thermostat in thermostats:
            if thermostat.should_update():
                thermostat.update()
                client.publish(thermostat.get_channel_prefix() + "mode", payload=thermostat.mode, qos=0, retain=False)
                client.publish(thermostat.get_channel_prefix() + "target_temp", payload=thermostat.target_temp, qos=0, retain=False)
                client.publish(thermostat.get_channel_prefix() + "current_temp", payload=thermostat.current_temp, qos=0, retain=False)

            time.sleep(5)
    
