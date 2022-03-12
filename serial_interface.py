import traceback
import sys
import serial
import time
import threading
import queue
import paho.mqtt.client as mqtt
import numpy as np

MQTT_SERVER="gork"
DEVICE=sys.argv[1]
TARGET=sys.argv[2]

XY_FEED=100

class SerialInterface(threading.Thread):
    
    def __init__(self, port=DEVICE, baud=115200):
        super().__init__()

        self.serialport = serial.serial_for_url(port, do_not_open=True)
        self.serialport.baudrate = baud
        self.serialport.parity = serial.PARITY_NONE
        self.serialport.stopbits=serial.STOPBITS_ONE
        self.serialport.bytesize=serial.EIGHTBITS
        self.serialport.dsrdtr= True
        self.serialport.dtr = True
       
        self.position_stack = []

        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)


    def run(self):
        self.client.loop_start()

        try:
            self.serialport.open()
        except serial.SerialException as e:
            sys.stderr.write("Could not open serial port {}: {}\n".format(ser.name, e))
            return
        #self.reset()
        
        self.status_thread = threading.Thread(target=self.get_status)
        self.status_thread.start()

        while True:
            message = self.serialport.readline()
            message = str(message, 'ascii').strip()
            if message == '':
                continue
            if message.startswith("<") and message.endswith(">"):
                rest = message[1:-3].split('|')
                self.state = rest[0]
                self.client.publish(f"{TARGET}/state", self.state)
                for item in rest:
                    if item.startswith("MPos"):
                        self.m_pos = [float(field) for field in item[5:].split(',')]
                        self.client.publish(f"{TARGET}/m_pos", str(self.m_pos))
                    elif item.startswith("WCO"):
                        self.w_pos = [float(field) for field in item[4:].split(',')]
                        self.client.publish(f"{TARGET}/w_pos", str(self.w_pos))
            else:
                sys.stdout.write(message)
                self.client.publish(f"{TARGET}/output", message)
            time.sleep(0.01)

    def get_status(self):
        while True:
            self.serialport.write(b"?")
            time.sleep(0.1) 

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect")
        self.client.subscribe(f"{TARGET}/command")
        self.client.subscribe(f"{TARGET}/reset")
        self.client.subscribe(f"{TARGET}/cancel")
        self.client.subscribe(f"{TARGET}/pos")
        self.client.subscribe(f"{TARGET}/grid")

    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/command":
            command = message.payload.decode("utf-8")
            if command == '?':
                self.write(command)
            else:
                print("Got command: ", command)
                self.write(command + "\n")
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
                    self.write(cmd)
        elif message.topic == f"{TARGET}/reset":
            if message.payload.decode("utf-8") == "hard":
                self.reset()
            else:
                self.soft_reset()
        elif message.topic == f"{TARGET}/grid":
            print("grid")
            self.grid()
        elif message.topic == f"{TARGET}/cancel":
            print("cancel")
            self.serialport.write(bytes([0x85]))
    
    def grid(self):
        try:
            pos0 = self.m_pos
            print(pos0)
            print(self.position_stack)
            try:
                pos1 = self.position_stack.pop()
            except IndexError:
                print("Stack empty")
                return
            half_fov = .25
            xs = np.arange(min(pos0[0], pos1[0]), max(pos0[0], pos1[0]), half_fov)
            ys = np.arange(min(pos0[1], pos1[1]), max(pos0[1], pos1[1]), half_fov)
            xx, yy = np.meshgrid(xs, ys)
            s_grid = np.vstack([xx.ravel(), yy.ravel()]).T
            print(s_grid)
            self.grid_thread = threading.Thread(target=self.grid_run, kwargs={"s_grid":  s_grid})
            self.grid_thread.start()
        except:
            traceback.print_exc()

    def grid_run(self, s_grid):
        print("grid run")
        for i, pos in enumerate(s_grid):
            print("grid thread visiting", pos)
            cmd = f"G0 X{pos[0]:.3f} Y{pos[1]:.3f} F{XY_FEED:.3f}\n"
            print(cmd)
            self.client.publish(f"{TARGET}/command", cmd)
            time.sleep(2)
            print("wait for idle")
            while self.state != 'Idle':
                time.sleep(1)
            self.client.publish(f"{TARGET}/photo", f"{pos[1]:08.3f}_{pos[0]:08.3f}.jpg")
            print("ending command loop", len(s_grid)-i, "remaining")
        print("grid done")
            
    def soft_reset(self):
        print("soft reset")
        self.serialport.write("\x18") # Ctrl-X

    def reset(self):
        print("reset\r")
        self.serialport.dtr = False
        time.sleep(.5)
        self.serialport.dtr = True


    def write(self, data):
        self.serialport.write(bytes(data,"utf-8"))
        self.serialport.flush()


def main():
    s = SerialInterface()
    s.start()
    s.join()    

if __name__ == "__main__":
    main()
