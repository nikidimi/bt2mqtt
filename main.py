import paho.mqtt.client as mqtt
import time
import logging
import yaml
import importlib

logging.basicConfig(level=logging.DEBUG)

def on_connect(client, userdata, flags, rc):
    for device in userdata:
        device.on_connect(client)

def create_device(device):
    device_module = importlib.import_module(f"devices.{device['type']}")
    device_class = getattr(device_module, device["type"].title())
    return device_class(device)


if __name__ == '__main__':
    stream = open("config.yaml", 'r')
    config = yaml.safe_load(stream)

    devices = [create_device(device) for device in config["devices"]]

    client = mqtt.Client(userdata=devices)
    client.on_connect = on_connect

    client.username_pw_set(username=config["mqtt"]["username"], password=config["mqtt"]["password"])
    client.connect(config["mqtt"]["host"], 1883, 60)
    client.publish("lwt_topic", payload="online", qos=0, retain=False)

    client.loop_start()

    while True:
        for device in devices:
            device.update_if_necessary(client)
            time.sleep(5)
    
