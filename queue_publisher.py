from io import BytesIO

import paho.mqtt.client as mqtt
import json

class QueuePublisher:

    def __init__(self):
        broker="iot.eclipse.org"
        self.client= mqtt.Client() 
        print("connecting to broker ",broker)
        self.client.connect(broker)#connect

    def publishResults(self,encoding,isUnwanted,chat_id,time):
        data = {}
        data["encoding"] = encoding
        data["isUnwanted"] = isUnwanted
        data["chat_id"] = chat_id
        data["time"] = time
        data_out=json.dumps(data) # encode object to JSON
        self.client.publish("masterResults",data_out)

    def stop(self):
        client.disconnect() #disconnect
        client.loop_stop() #stop loop