import sys
import serial
import time
import threading
import queue
import paho.mqtt.client as mqtt

MQTT_SERVER="inspectionscope.local"
WEBSOCKET_SERVER=sys.argv[1]

class SerialInterface(threading.Thread):
    
    def __init__(self, port="/dev/ttyUSB0", baud=115200):
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
        self.client.loop_start()
        self.client.connect(MQTT_SERVER)

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/command")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/reset")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/cancel")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/pos")
        self.client.subscribe(f"{WEBSOCKET_SERVER}/grid")

    def on_message(self, client, userdata, message):
        if message.topic == f"{WEBSOCKET_SERVER}/command":
            command = message.payload.decode("utf-8")
            if command == '?':
                self.write(command)
            else:
                print("Got command: ", command)
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
        elif message.topic == f"{WEBSOCKET_SERVER}/reset":
            if message.payload.decode("utf-8") == "hard":
                self.reset()
            else:
                self.soft_reset()
        elif message.topic == f"{WEBSOCKET_SERVER}/grid":
            print("grid")
            self.grid()
        elif message.topic == f"{WEBSOCKET_SERVER}/cancel":
            print("cancel")
            self.serialport.write(bytes([0x85]))
            
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
        print("soft reset")
        self.serialport.write("\x18") # Ctrl-X

    def reset(self):
        print("reset\r")
        self.serialport.dtr = False
        time.sleep(.5)
        self.serialport.dtr = True

    def run(self):
        try:
            self.serialport.open()
        except serial.SerialException as e:
            sys.stderr.write("Could not open serial port {}: {}\n".format(ser.name, e))
            return
        self.serialport.write(b"?")
        #self.reset()
        
        while True:
            if self.serialport.in_waiting > 0:
                data = self.serialport.read(self.serialport.in_waiting)
                sys.stdout.write(data.decode("utf-8"))
                self.client.publish(f"{WEBSOCKET_SERVER}/output", data)
            time.sleep(0.01)

    def write(self, data):
        self.serialport.write(bytes(data,"utf-8"))
        self.serialport.flush()


def main():
    s = SerialInterface()
    s.start()
    s.join()    

if __name__ == "__main__":
    main()
