import time
import threading
import numpy as np
import json
import paho.mqtt.client as mqtt
import sys

MQTT_SERVER="gork.local"
TARGET=sys.argv[1]
XY_FEED=25
half_fov = .15

class Grid():
    
    def __init__(self):
        super().__init__()


        self.client =  mqtt.Client()

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)

        self.m_pos = None
        self.state = None
        self.grid = []
        self.position_stack = []

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(f"{TARGET}/grid")
        self.client.subscribe(f"{TARGET}/state")
        self.client.subscribe(f"{TARGET}/m_pos")
        self.client.subscribe(f"{TARGET}/pos")


    def on_message(self, client, userdata, message):
        if message.topic == f'{TARGET}/state':
            self.state = str(message.payload, 'ascii').strip()
        elif message.topic == f"{TARGET}/pos":
            if message.payload.decode('utf-8') == 'push':
                if self.m_pos is not None:
                    print("push", self.m_pos)
                    self.position_stack.append(self.m_pos)
                    print("Stack now:", self.position_stack)
                else:
                    print("Unable to push, no status")
            elif message.payload.decode('utf-8') == 'pop':
                if len(self.position_stack) == 0:
                    print("Stack empty.")
                else:
                    new_pos = self.position_stack.pop()
                    print("pop", new_pos)
                    x = new_pos[0] - self.m_pos[0]
                    y = new_pos[1] - self.m_pos[1]
                    cmd = f"$J=G91 X{x:.3f} Y{y:.3f} F{XY_FEED:.3f}\n"
                    self.client.publish(f"{TARGET}/command", cmd)
        elif message.topic == f'{TARGET}/m_pos':
            self.m_pos = json.loads(message.payload)
        
        elif message.topic == f'{TARGET}/grid':
            if not self.grid or not self.grid.is_alive():
                pos0 = self.m_pos
                try:
                    pos1 = self.position_stack.pop()
                except IndexError:
                    print("Stack empty")
                    return
                x_min = min(pos0[0], pos1[0])
                x_max = max(pos0[0], pos1[0])
                y_min = min(pos0[1], pos1[1])
                y_max = max(pos0[1], pos1[1])
                
                print("upper_right: ", x_max, y_max)
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
                
                self.grid = threading.Thread(target=self.grid_run, args=[s_grid])
                self.grid.start()

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
            self.client.publish(f"{TARGET}/photo", f"{pos[1]:08.3f}_{pos[0]:08.3f}.jpg")
            print("ending command loop", len(s_grid)-i, "remaining")
        print("grid done")



def main():
    g = Grid()
    g.client.loop_forever()

if __name__ == "__main__":
    main()
