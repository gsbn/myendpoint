import socket
import os
import json
import bluelibrary, myendpoint
from datetime import datetime
from bluepy.btle import Scanner, DefaultDelegate, BTLEDisconnectError, BTLEInternalError # pip install bluepy
import paho.mqtt.client as mqtt_client # pip install paho-mqtt
import paho.mqtt.publish as mqtt_publish

# Settings
with open(os.path.dirname(__file__) + '/config.json') as f:
    config = json.load(f)
mqtt_host = config['mqtt_host']
mqtt_port = config['mqtt_port']
mqtt_topic_keys = config['mqtt_topic_keys']
mqtt_topic_endpoints = config['mqtt_topic_endpoints']
mqtt_username = config['mqtt_username']
mqtt_password = config['mqtt_password']
if len(mqtt_username) > 0:
    mqtt_auth = { 'username': mqtt_username, 'password': mqtt_password }
else:
    mqtt_auth = None

# BLE Data Processor
def ProcessDevice(dev):
    global myip, ble_keys, mqtt_auth
    ble_dict = bluelibrary.ProcessRawData(dev.rawData, ble_keys)
    # Add timestamp
    dt = datetime.now()
    ts = int(round(datetime.timestamp(dt)*1000))
    ble_dict['timestamp'] = ts
    # Add current IP address
    ble_dict['detector'] = myip
    # Add RSSI Strength
    ble_dict['rssi'] = dev.rssi
    # Known device
    if "debug" in ble_dict:
        # Debug device for testing
        #print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData[0:15].hex()+"...")
        json_data = json.dumps(ble_dict, indent = 4)
        #print(json_data)
    elif "device" in ble_dict:
        json_data = json.dumps(ble_dict, indent = 4)
        print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData[0:15].hex()+"...")
        try:
            mqtt_publish.single('ble/'+ble_dict['mac'][-4:], json_data, qos=2, retain=True, hostname=mqtt_host, port=mqtt_port, auth=mqtt_auth)
        except:
            print("MQTT Publish Single Error")
    #else:
        #print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData[0:15].hex()+"...")

### MQTT
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            print("Failed to connect, return code %d\n", rc)
        else:
            print("Connected to MQTT Broker!")

    client = mqtt_client.Client()
    client.on_connect = on_connect
    if len(mqtt_username) > 0:
        client.username_pw_set(username=mqtt_username,password=mqtt_password)
    try:
        client.connect(mqtt_host, mqtt_port)
    except:
        print("MQTT Server Error")

    return client

def subscribe_mqtt(client: mqtt_client):
    def on_message(client, userdata, msg):
        global ble_keys
        ble_keys = json.loads(msg.payload)
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(mqtt_topic_keys)
    client.on_message = on_message

### Main classes
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        global scanner
        ProcessDevice(dev)
        scanner.clear()
        scanner.start()

### Main
def main():
    print("Started!")

    # Get IP address
    global myip, scanner
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1", 80))
    myip = s.getsockname()[0]
    s.close()

    # MQTT
    client = connect_mqtt()
    subscribe_mqtt(client)
    client.loop_start()

    # Loop
    curr_minute = 0
    scanner = Scanner().withDelegate(ScanDelegate())
    scanner.start()
    while True:
        # Endpoint status once a minute
        if datetime.now().minute != curr_minute:
            curr_minute = datetime.now().minute
            json_data = myendpoint.main()
            mqtt_publish.single(mqtt_topic_endpoints + '/' + myip, json_data, qos=0, retain=False, hostname=mqtt_host, port=mqtt_port, auth=mqtt_auth)
            print("Endpoint status sent")

        # BLE Scanner
        try:
            scanner.process()
        except BTLEDisconnectError:
            print("BTLE Disconnect Error")
            scanner.clear()
            scanner.start()
        except BTLEInternalError:
            print("BTLE Internal Error")

if __name__ == "__main__":
    main()