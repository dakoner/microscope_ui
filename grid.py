import time
import threading
import numpy as np
import json
import paho.mqtt.client as mqtt
import sys

MQTT_SERVER="gork.local"
TARGET=sys.argv[1]
XY_FEED=25
half_fov = .3

class Grid():
    
    def __init__(self):
        super().__init__()


        self.client =  mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)

        self.m_pos = None
        self.state = None
    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(f"{TARGET}/makegrid")
        self.client.subscribe(f"{TARGET}/state")
        self.client.subscribe(f"{TARGET}/m_pos")


    def on_message(self, client, userdata, message):
        if message.topic == f'{TARGET}/state':
            self.state = str(message.payload, 'ascii').strip()
        if message.topic == f'{TARGET}/m_pos':
            self.m_pos = json.loads(message.payload)
        
        elif message.topic == f'{TARGET}/makegrid':
            [x_min, x_max, y_min, y_max] = json.loads(message.payload)
            
            print("upper_right: ", x_min, y_max)
            print("lower_left: ", x_max, y_min)
            travel_x = x_max - x_min
            travel_y = y_max - y_min
            print("travel:", travel_x, travel_y)
            cmd = f"G92 X{self.m_pos[0]:.3f} Y{self.m_pos[1]:.3f}"
            self.client.publish(f'{TARGET}/command', cmd)

            xs = np.arange(x_min, x_max, half_fov)
            ys = np.arange(y_min, y_max, half_fov)
            xx, yy = np.meshgrid(xs, ys)
            s_grid = np.vstack([xx.ravel(), yy.ravel()]).T
            self.grid_thread = threading.Thread(target=self.grid_run, kwargs={"s_grid":  s_grid})
            self.grid_thread.start()

    def grid_run(self, s_grid):
        print("grid run")
        for i, pos in enumerate(s_grid):
            print("grid thread visiting", pos)
            cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{pos[0]:.3f} Y{pos[1]:.3f}\n"
            print(cmd)
            self.client.publish(f"{TARGET}/command", cmd)
            print("wait for jog")
            t0 = time.time()
            while self.state != 'Jog' and time.time()-t0 < 1:
                time.sleep(0.25)
            print("wait for idle")
            while self.state != 'Idle':
                time.sleep(0.25)
            print("idle, wait for settle")
            time.sleep(1)
            #self.client.publish(f"{TARGET}/photo", f"{pos[1]:08.3f}_{pos[0]:08.3f}.jpg")
            print("ending command loop", len(s_grid)-i, "remaining")
        print("grid done")



def main():
    g = Grid()
    g.client.loop_forever()

if __name__ == "__main__":
    main()
