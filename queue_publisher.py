from io import BytesIO

import paho.mqtt.client as mqtt
import json
import time
import configparser
class QueuePublisher:

    def __init__(self):
        parser = configparser.ConfigParser()
        parser.read('config.ini')
        self.client = mqtt.Client() 
        url = parser.get('mqtt_broker', 'url')
        port = parser.getint('mqtt_broker', 'port')
        username = parser.get('mqtt_broker', 'username')
        password = parser.get('mqtt_broker', 'password')
        print("connecting to broker ",url)
        self.client.username_pw_set(username, password)
        self.client.connect(url,port)

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