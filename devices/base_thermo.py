import time
import json
from bluepy import btle
from threading import Lock


class BaseThermo:
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

    def __update_device(self):
        self._current_mode = None
        self._current_temp = None
        self._current_target_temp = None


        try:
            with self._target_temp_lock:
                if self._target_temp is not None:
                    self._conn.target_temperature  = self._target_temp
            self._conn.update()
        except (BrokenPipeError, btle.BTLEDisconnectError, UnicodeDecodeError):
            pass
        else:
            self._current_mode = "heat"
            if self.supports_current_temp:
                self._current_temp = self._conn.current_temperature
            self._current_target_temp = self._conn.target_temperature


            self._last_update = time.time()
            with self._target_temp_lock:
                self._target_temp = None

    def update_if_necessary(self, client):
        if self.should_update():
            self.__update_device()
            client.publish(self.get_channel_prefix() + "mode", payload=self.mode, qos=0, retain=False)
            client.publish(self.get_channel_prefix() + "target_temp", payload=self.target_temp, qos=0, retain=False)
            client.publish(self.get_channel_prefix() + "current_temp", payload=self.current_temp, qos=0, retain=False)



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

    def on_message(self, lient, userdata, message):
        self.target_temp = float(message.payload)
        print(message.topic+" "+str(message.payload))

    def on_connect(self, client):
        client.subscribe(self.get_channel_prefix() + "target_temp/set")
        client.message_callback_add(self.get_channel_prefix() + "target_temp/set", self.on_message)
        client.publish("homeassistant/climate/" + self.get_id() + "/config", payload=json.dumps(self.get_data()), qos=0, retain=False)
        