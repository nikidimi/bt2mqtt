import time
import json
import sys
import RPi.GPIO as GPIO
from threading import Lock

NUM_ATTEMPTS = 5 
TRANSMIT_PIN = 17

class Rf433:
    def __init__(self, config):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
        self._code = config["code"]
        self._id = config["name"]
        self._delay = config["delay"]
        self._repeat_delay = config["repeat_delay"]

    def get_channel_prefix(self):
        return "gpio/" + self._id + "/"

    def get_data(self):
        data = {     
            "unique_id": self._id,

            "command_topic": self.get_channel_prefix() +  "set",

            "device":{
                "identifiers":[
                    self._id,
                ],
            }
        }

        return data

    def update_if_necessary(self, client):
        pass

    def get_id(self):
        return self._id

    def on_message(self, lient, userdata, message):
        for t in range(NUM_ATTEMPTS):
            for i in self._code:
                if i == '1':
                    GPIO.output(TRANSMIT_PIN, 1)
                    time.sleep(self._delay)
                elif i == '0':
                    GPIO.output(TRANSMIT_PIN, 0)
                    time.sleep(self._delay)
                else:
                    continue
            GPIO.output(TRANSMIT_PIN, 0)
            time.sleep(self._repeat_delay)

    def on_connect(self, client):
        client.subscribe(self.get_channel_prefix() + "set")
        client.message_callback_add(self.get_channel_prefix() + "set", self.on_message)
        client.publish("homeassistant/switch/" + self.get_id() + "/thermo-test-ht100/config", payload=json.dumps(self.get_data()), qos=0, retain=False)