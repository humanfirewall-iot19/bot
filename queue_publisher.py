from io import BytesIO

import paho.mqtt.client as mqtt


class QueuePublisher:
    broker="localhost"

    def __init__(self, token, db_path=None):
        self.client= paho.Client("client-001") #create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")
        self.client.on_message=on_message
        print("connecting to broker ",broker)
        self.client.connect(broker)#connect
        self.client.publish("masterResults","on")#publish
        time.sleep(4)

    def publishResults(encoding,isUnwanted,chat_id,time):
        data = {}
        data["encoding"] = encoding
        data["isUnwanted"] = isUnwanted
        data["chat_id"] = chat_id
        data["time"] = time
        data_out=json.dumps(brokers_out) # encode object to JSON
        self.client.publish("masterResults",data_out)

    def stop(self):
        client.disconnect() #disconnect
        client.loop_stop() #stop loop