import sys
import serial
import time
import threading
import queue
import paho.mqtt.client as mqtt
import numpy as np

import websocket
import threading

MQTT_SERVER="inspectionscope.local"
WEBSOCKET_SERVER=sys.argv[1]
XY_STEP_SIZE=500
Z_STEP_SIZE=.01
Z_FEED=500
XY_FEED=1000

class WebSocketInterface():
    def __init__(self):
        super().__init__()

        self.wsapp = websocket.WebSocketApp(
            f"ws://{WEBSOCKET_SERVER}:81", 
            on_open=self.on_ws_connect, 
            on_message=self.on_ws_message, 
            on_close=self.on_ws_close)

        self.position_stack = []

        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER, 1883, 60)


    def run(self):
        self.client.loop_start()
        self.wsapp.run_forever()
        #self.client.loop_forever()
        # while True:
        #     self.client.loop()
        
    def on_ws_connect(self, ws):
        print(">>>>>OPENED")

        self.status_thread = threading.Thread(target=self.get_status)
        self.status_thread.start()

        self.m_pos = None
        self.w_pos = None

    def get_status(self):
        while True:
            try:
                self.write(b"?")
            except websocket._exceptions.WebSocketConnectionClosedException:
                print("Connection terminated.  Stopping status checks")
                return
            time.sleep(1)

    def on_ws_message(self, ws, message):
        try:
            if isinstance(message, str):
                if message.startswith("CURRENT_ID"):
                    self.current_id = message.split(':')[1]
                elif message.startswith("ACTIVE_ID"):
                    active_id = message.split(':')[1]
                    if self.current_id != active_id:
                        print("Warning: different active id.")
                elif message.startswith("PING"):
                    ping_id = message.split(":")[1]
                    if ping_id != self.current_id:
                        print("Warning: ping different active id.")
            else:
                message = str(message, 'ascii')
                for m in message.split("\n"):
                    if m != '':
                        if m.startswith("<") and m.endswith(">"):
                            rest = m[1:-3].split('|')
                            self.state = rest[0]
                            self.client.publish(f"{WEBSOCKET_SERVER}/state", self.state)
                            for item in rest:
                                if item.startswith("MPos"):
                                    self.m_pos = [float(field) for field in item[5:].split(',')]
                                    self.client.publish(f"{WEBSOCKET_SERVER}/m_pos", str(self.m_pos))
                                elif item.startswith("WCO"):
                                    self.w_pos = [float(field) for field in item[4:].split(',')]
                                    self.client.publish(f"{WEBSOCKET_SERVER}/w_pos", str(self.w_pos))
                        self.client.publish(f"{WEBSOCKET_SERVER}/output", m)
        except Exception as e:
            print("Caught exception", e)
            
    def on_ws_close(self, ws, close_status_code, close_msg):
        print(">>>>>>CLOSED")
   

    def on_connect(self, client, userdata, flags, rc):
        print("on connect")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/command")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/reset")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/cancel")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/pos")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/grid")

    def on_message(self, client, userdata, message):
        print(message.topic, message.payload)
        if message.topic == f"{WEBSOCKET_SERVER}/command":
            command = message.payload.decode('utf-8')
            if command == '?':
                self.write(command)
            else:
                self.write(command + "\n")
        elif message.topic == f"{WEBSOCKET_SERVER}/pos":
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
                    self.write(cmd)
        elif message.topic == f"{WEBSOCKET_SERVER}/grid":
            print("grid")
            self.grid()
        elif message.topic == f"{WEBSOCKET_SERVER}/reset":
            if message.payload.decode('utf-8') == 'hard':
                self.reset()
            else:
                self.soft_reset()
        elif message.topic == f"{WEBSOCKET_SERVER}/cancel":
            self.write(chr(0x85))
            
    def grid(self):
        pos0 = self.m_pos
        print(pos0)
        print(self.position_stack)
        try:
            pos1 = self.position_stack.pop()
        except IndexError:
            print("Stack empty")
            return
        half_fov = 1.6
        xs = np.arange(min(pos0[0], pos1[0]), max(pos0[0], pos1[0]), half_fov)
        ys = np.arange(min(pos0[1], pos1[1]), max(pos0[1], pos1[1]), half_fov)
        xx, yy = np.meshgrid(xs, ys)
        s_grid = np.vstack([xx.ravel(), yy.ravel()]).T
        self.grid_thread = threading.Thread(target=self.grid_run, kwargs={"s_grid":  s_grid})
        self.grid_thread.start()

    def grid_run(self, s_grid):
        print("grid run")
        for i, pos in enumerate(s_grid):
            print("grid thread visiting", pos)
            cmd = f"G0 X{pos[0]:.3f} Y{pos[1]:.3f} F{XY_FEED:.3f}\n"
            print(cmd)
            self.client.publish(f"{WEBSOCKET_SERVER}/command", cmd)
            time.sleep(2)
            print("wait for idle")
            while self.state != 'Idle':
                time.sleep(1)
            self.client.publish(f"{WEBSOCKET_SERVER}/photo", f"{pos[1]:08.3f}_{pos[0]:08.3f}.jpg")
            print("ending command loop", len(s_grid)-i, "remaining")
        print("grid done")

    def soft_reset(self):
        self.write("\x18") # Ctrl-X

    def reset(self):
        self.write("[ESP444]RESTART\n")

    def write(self, data):
        self.wsapp.send(data)

def main():
    s = WebSocketInterface()
    s.run()

if __name__ == '__main__':
    main()
