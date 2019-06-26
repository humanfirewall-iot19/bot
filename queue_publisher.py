from io import BytesIO

import paho.mqtt.client as mqtt
import json
import time
import configparser
class QueuePublisher:

    def __init__(self, ip):
        parser = configparser.ConfigParser()
        parser.read('config.ini')
        self.client = mqtt.Client() 
        print("connecting to broker ",url)
        self.client.connect(ip,1883)

    def publishResults(self,encoding,isUnwanted,chat_id,time):
        data = {}
        data["encoding"] = encoding
        data["isUnwanted"] = isUnwanted
        data["chat_id"] = chat_id
        data["time"] = time
        data_out=json.dumps(data) # encode object to JSON
        self.client.publish("masterResults",data_out)
        print("sent ",data_out)

    def stop(self):
        client.disconnect() #disconnect
        client.loop_stop() #stop loop