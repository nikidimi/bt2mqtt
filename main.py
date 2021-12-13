import paho.mqtt.client as mqtt
import json
import time
import logging
import yaml

logging.basicConfig(level=logging.DEBUG)

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
        from devices.eq3 import Eq3Thermo 
        return Eq3Thermo(device["mac"])
    elif device["type"] == "sygonix":
        from devices.sygonix import SygonixThermo
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
    
