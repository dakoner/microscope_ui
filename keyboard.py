#!/usr/bin/python3
import signal
import time
import paho.mqtt.client as mqtt

from inputs import devices
from inputs import get_key
import threading
from queue import Queue, Empty
import math

STEP_SIZE=0.5
TARGET="inspection-6pack.local"
MQTT_SERVER="inspectionscope.local"
XY_STEP_SIZE=500
Z_STEP_SIZE=.01
Z_FEED=500
XY_FEED=1000

class Driver:
    def __init__(self):
        self.client =  mqtt.Client("client")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.connect(MQTT_SERVER)
        self.client.loop_start()

        self.queue = Queue()

        t = threading.Thread(target=self.keyboard)
        t.start()

    def keyboard(self):
        while True:
            events = get_key()
            self.queue.put(events)
 
    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True

    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
        self.timer.stop()


    def run(self):
        while True:
            try:
                events = self.queue.get(timeout=0.1)
                for event in events:
                    if event.ev_type == 'Key':
                        if event.code == 'KEY_KPENTER' and event.state == 1:
                            self.client.publish(f"{TARGET}/pos", "push")
                            continue
                        elif event.code == 'KEY_BACKSPACE' and event.state == 1:
                            self.client.publish(f"{TARGET}/pos", "pop")
                            continue
                        if event.code in ('KEY_KPMINUS', 'KEY_KPPLUS', 'KEY_KP2', 'KEY_KP4', 'KEY_KP6', 'KEY_KP8'):
                            if event.state == 0:
                                self.client.publish(f"{TARGET}/cancel")
                                continue          
                            if event.state == 2:
                                continue       
                            else:
                                if event.code == 'KEY_KPMINUS':
                                    cmd = f"$J=G91 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                                    self.client.publish(f"{TARGET}/command", cmd)
                                elif event.code == 'KEY_KPPLUS' and event.state == 1:
                                    cmd = f"$J=G91 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                                    self.client.publish(f"{TARGET}/command", cmd)
                                elif event.code == 'KEY_KP2' and event.state == 1:
                                    cmd = f"$J=G91 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                                    self.client.publish(f"{TARGET}/command", cmd)
                                elif event.code == 'KEY_KP8' and event.state == 1:
                                    cmd = f"$J=G91 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                                    self.client.publish(f"{TARGET}/command", cmd)
                                elif event.code == 'KEY_KP4' and event.state == 1:
                                    cmd = f"$J=G91 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                                    self.client.publish(f"{TARGET}/command", cmd)
                                elif event.code == 'KEY_KP6' and event.state == 1:
                                    cmd = f"$J=G91 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                                    self.client.publish(f"{TARGET}/command", cmd)
                                else:
                                    self.client.publish(f"{TARGET}/cancel")
            except Empty:
                pass
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    d = Driver()
    d.run()
 
