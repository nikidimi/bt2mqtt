# bt2mqtt

This is a simple python script to allow control of various devices from Home Assistant via MQTT.
It's very similar to https://github.com/zewelor/bt-mqtt-gateway, however my BLE devices are far from my RPi and this project tries to handle disconnects better. The major difference is that I don't connect to multiple BLE devices in parallel, they are always queried  sequentially. It also continues running on most errors