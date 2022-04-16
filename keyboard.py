#!/usr/bin/python3
import signal
import time
import paho.mqtt.client as mqtt

from inputs import devices
from inputs import get_key
from queue import Queue, Empty
import math
import sys

STEP_SIZE=0.5
TARGET=sys.argv[1]
MQTT_SERVER="gork.local"
XY_STEP_SIZE=32
XY_FEED=50

Z_STEP_SIZE=15
Z_FEED=1

class Driver:
    def __init__(self):
        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.connect(MQTT_SERVER)
        self.client.loop_start()
 
    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True

    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
        self.timer.stop()

    def run(self):
        while True:
            events = get_key()
            for event in events:
                if event.ev_type == 'Key':
                    if event.code == 'KEY_KPENTER' and event.state == 1:
                        self.client.publish(f"{TARGET}/cancel")
                        self.client.publish(f"{TARGET}/pos", "push")
                    elif event.code == 'KEY_BACKSPACE' and event.state == 1:
                        self.client.publish(f"{TARGET}/cancel")
                        self.client.publish(f"{TARGET}/pos", "pop")
                    elif event.code == 'KEY_KP0' and event.state == 1:
                        self.client.publish(f"{TARGET}/grid", "foo")
                    elif event.code == 'KEY_KP5' and event.state == 1:
                        print("Cancel")
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.code == 'KEY_KP7' and event.state == 1:
                        self.client.publish(f"{TARGET}/command", "M3S1000")
                    elif event.code == 'KEY_KP9' and event.state == 1:
                        self.client.publish(f"{TARGET}/command", "M5")
                    elif event.code == 'KEY_KPASTERISK' and event.state == 1:
                        self.client.publish(f"{TARGET}/track", "true")
                    elif event.code == 'KEY_KPSLASH' and event.state == 1:
                        self.client.publish(f"{TARGET}/track", "false")
                    elif event.code == 'KEY_KPDOT' and event.state == 1:
                        self.client.publish(f"{TARGET}/photo", "%s.jpg" % time.strftime("%Y%m%d-%H%M%S"))
                    elif event.code in ('KEY_KPMINUS', 'KEY_KPPLUS'):
                        if event.state == 0:
                            self.client.publish(f"{TARGET}/cancel")
                        elif event.state == 2:
                            pass       
                        else:
                            self.client.publish(f"{TARGET}/cancel")
                            if event.code == 'KEY_KPMINUS' and event.state == 1:
                                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                                self.client.publish(f"{TARGET}/command", cmd)
                            elif event.code == 'KEY_KPPLUS' and event.state == 1:
                                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                                self.client.publish(f"{TARGET}/command", cmd)        
                    elif event.code in ('KEY_KP2', 'KEY_KP4', 'KEY_KP6', 'KEY_KP8'):
                        if event.state == 0:
                            self.client.publish(f"{TARGET}/cancel")          
                        elif event.state == 2:
                            pass       
                        else:
                            self.client.publish(f"{TARGET}/cancel")
                            if event.code == 'KEY_KP2' and event.state == 1:
                                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                                self.client.publish(f"{TARGET}/command", cmd)
                            elif event.code == 'KEY_KP8' and event.state == 1:
                                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                                self.client.publish(f"{TARGET}/command", cmd)
                            elif event.code == 'KEY_KP4' and event.state == 1:
                                cmd = f"$J=G91  G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                                self.client.publish(f"{TARGET}/command", cmd)
                            elif event.code == 'KEY_KP6' and event.state == 1:
                                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                                self.client.publish(f"{TARGET}/command", cmd)
                    else:
                        print(event.code, event.state)
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    d = Driver()
    d.run()
 
