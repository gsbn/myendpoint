import socket
import json
import bluelibrary
from datetime import datetime
from secrets import secrets
from bluepy.btle import Scanner, DefaultDelegate, BTLEDisconnectError, BTLEInternalError # pip install bluepy
import paho.mqtt.client as mqtt_client # pip install paho-mqtt
import paho.mqtt.publish as mqtt_publish

# Global Constants
udp_host = "10.2.0.23"
udp_port = 1888
mqtt_host = secrets.get('mqtt_host') # "10.2.0.24"
mqtt_port = secrets.get('mqtt_port') # 1883
mqtt_topic_keys = secrets.get('mqtt_topic_keys') # "avening/ble/keys"
mqtt_username = secrets.get('mqtt_username')
mqtt_password = secrets.get('mqtt_password')
ble_keys = {}

# Network TCP and UDP
def send_tcp_msg(address, port, sdata):
    msgdata = b""
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_sock.connect((address, port))
        tcp_sock.send(bytes(sdata + "\r\n", "ascii"))
        msgdata = tcp_sock.recv(2048)
    except socket.error:
        print("TCP Socket Error")
    finally:
        tcp_sock.close()
    return msgdata

def send_udp_msg(address, port, sdata):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.settimeout(10)
    try:
        udp_sock.sendto(bytes(sdata, "utf-8"), (address, port))
    except socket.error:
        print("UDP Socket error")

# BLE Data Processor
def ProcessDevice(dev):
    ble_dict = bluelibrary.ProcessRawData(dev.rawData, ble_keys)
    # Add timestamp
    dt = datetime.now()
    ts = int(round(datetime.timestamp(dt)*1000))
    ble_dict['timestamp'] = ts
    # Add current IP address
    ble_dict['detector'] = myip
    # Known device
    if "debug" in ble_dict:
        # Debug device for testing
        #print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData[0:15].hex()+"...")
        #print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData.hex())
        json_data = json.dumps(ble_dict, indent = 4)
        #print(json_data)
    elif "device" in ble_dict:
        json_data = json.dumps(ble_dict, indent = 4)
        print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData[0:15].hex()+"...")
        #send_udp_msg(udp_host, udp_port, json_data)
        mqtt_auth = None
        if len(mqtt_username) > 0:
            mqtt_auth = { 'username': mqtt_username, 'password': mqtt_password }
        try:
            mqtt_publish.single('avening/ble/'+ble_dict['mac'][-4:], json_data, qos=2, retain=True, hostname=mqtt_host, port=mqtt_port, auth=mqtt_auth)
        except:
            print("MQTT Publish Single Error")
    #else:
        #print(datetime.now().time(), dev.addr, dev.addrType, dev.rssi, dev.rawData[0:15].hex()+"...")

### MQTT
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            print("Failed to connect, return code %d\n", rc)
        #else:
            #print("Connected to MQTT Broker!")

    client = mqtt_client.Client("python_mqtt_client")
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
        #print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(mqtt_topic_keys)
    client.on_message = on_message


### Main classes
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        ProcessDevice(dev)
        scanner.clear()
        scanner.start()


### Main
print("Started!")
myhostname = socket.gethostname()
myip = socket.gethostbyname(myhostname)
# MQTT
client = connect_mqtt()
subscribe_mqtt(client)
client.loop_start()
# BLE
scanner = Scanner().withDelegate(ScanDelegate())
scanner.start()
while True:
    try:
        scanner.process()
    except BTLEDisconnectError:
        print("BTLEDisconnectError")
        scanner.clear()
        scanner.start()
    except BTLEInternalError:
        print("BTLEInternalError")
