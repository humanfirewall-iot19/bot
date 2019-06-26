from io import BytesIO

import paho.mqtt.client as mqtt
import json
import time
import configparser


class QueuePublisher:

    def __init__(self, ip):
        self.client = mqtt.Client()
        print("connecting to broker ", ip)
        self.client.connect(ip, 1883)
        self.client.loop_start()

    def publishResults(self, encoding, isUnwanted, chat_id, time):
        data = {}
        data["encoding"] = encoding
        data["isUnwanted"] = isUnwanted
        data["chat_id"] = chat_id
        data["time"] = time
        data_out = json.dumps(data)  # encode object to JSON
        ret = self.client.publish("masterResults", data_out)
        print("sent ", data_out, "error code", ret[0])

    def stop(self):
        self.client.disconnect()  # disconnect
        self.client.loop_stop()  # stop loop
