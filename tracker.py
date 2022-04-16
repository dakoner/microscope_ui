import time
import threading
import numpy as np
import json
import paho.mqtt.client as mqtt
import sys
import os

MQTT_SERVER="gork.local"
TARGET=sys.argv[1]
XY_FEED=25
pixel_to_mm = 0.00005


class Tracker():       
    def __init__(self):
        print("a")
        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)

        self.tracking = False
     
    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/inference":
            results = json.loads(message.payload)
            size = np.array(results['size'][:2])
            first = True
            for score, label, box in results['results']:
                if label == 'tardigrade' and score > 0.98 and first:
                    box = np.array(box)
                    box_center = (box[1] - box[0])/2
                    print("box_center", box_center)
                    image_center = size/2
                    print("image_center", image_center)
                    dt = box_center - image_center
                    cmd = "$J=G91  G21  F%.3f X%.3f Y%.3f"% (XY_FEED, -dt[0]*pixel_to_mm, -dt[1]*pixel_to_mm)
                    if self.tracking:
                        print("tracking with cmd", cmd)
                        # self.client.publish(f"{TARGET}/cancel")
                        self.client.publish(f"{TARGET}/command", cmd)
                    else:
                        print("not tracking")
                    first = False

        elif message.topic == f"{TARGET}/track":
            if message.payload == b'true':
                print("start tracking")
                self.tracking = True
            elif message.payload == b'false':
                print("stop tracking")
                self.tracking = False
            else:
                print("unknown payload", message.payload)

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True
        self.client.subscribe(f"{TARGET}/track")
        self.client.subscribe(f"{TARGET}/inference")
        



if __name__ == "__main__":
    t = Tracker()
    print(dir(t))
    t.client.loop_forever()
