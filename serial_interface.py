import imagezmq
import simplejpeg
import cv2
import sys
import serial
import time
import threading
import paho.mqtt.client as mqtt
from config import WIDTH, HEIGHT, FPS
MQTT_SERVER="raspberrypi"
DEVICE=sys.argv[1]
TARGET=sys.argv[2]
IMAGE_TIMEOUT=0.03
STATUS_TIMEOUT=0.03
XY_FEED=5

def openSerial(port, baud):
    serialport = serial.serial_for_url(port, do_not_open=True)
    serialport.baudrate = baud
    serialport.parity = serial.PARITY_NONE
    serialport.stopbits=serial.STOPBITS_ONE
    serialport.bytesize=serial.EIGHTBITS
    serialport.dsrdtr= True
    serialport.dtr = True
    
    try:
        serialport.open()
    except serial.SerialException as e:
        sys.stderr.write("Could not open serial port {}: {}\n".format(serialport.name, e))
        raise

    return serialport

class SerialInterface:
    
    def __init__(self, port=DEVICE, baud=115200):
        super().__init__()
        self.status_time = time.time()
        self.serialport = openSerial(port, baud)
        self.startMqtt()
        self.status = None
        self.startStatusThread()
        self.startImageThread()

    def startImageThread(self):
        self.image_thread = threading.Thread(target=self.get_image)
        self.image_thread.start()

    def get_image(self):
        cap = cv2.VideoCapture('/dev/video0', 0)
        port = 5000
        cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc('M','J','P','G'))
        cap.set(cv2.CAP_PROP_FPS, FPS)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)
        counter = 0
        t0 = time.time()
        
        while True:
            ret = cap.grab()
            if ret:
                t1 = time.time()
                if t1 - t0 >= IMAGE_TIMEOUT:
                    # self.state = 'Idle'
                    # self.m_pos = 0, 0, 0
                    message = '{"state": "%s", "m_pos": [%8.3f, %8.3f, %8.3f]}' %  (self.state, *self.m_pos[:3])
                    ret, img = cap.retrieve()
                    if ret:
                        jpg_buffer = simplejpeg.encode_jpeg(img, quality=100, colorspace='BGR')
                        sender.send_jpg(message, jpg_buffer)
                        t0 = t1
                counter += 1
        
    def startStatusThread(self):
        self.status_thread = threading.Thread(target=self.get_status)
        self.status_thread.start()

    def startMqtt(self):
        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)

        self.client.loop_start()

        
    def readline(self):
        message = self.serialport.readline()
        message = str(message, 'utf8').strip()
        if message == '':
            return
        if message.startswith("<") and message.endswith(">"):
            # print("STATUS:", message)
            rest = message[1:-3].split('|')
            self.state = rest[0]
            self.client.publish(f"{TARGET}/state", self.state)
            t = time.time()
            self.status_time = t
            for item in rest:
                if item.startswith("MPos"):
                    self.m_pos = [float(field) for field in item[5:].split(',')]
                    self.client.publish(f"{TARGET}/m_pos", str(self.m_pos))
                elif item.startswith("WCO"):
                    self.w_pos = [float(field) for field in item[4:].split(',')]
                    self.client.publish(f"{TARGET}/w_pos", str(self.w_pos))
        else:
            print("OUTPUT:", message)
            self.client.publish(f"{TARGET}/output", message)

    def get_status(self):
        while True:
            self.serialport.write(b"?")
            time.sleep(STATUS_TIMEOUT)

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect")
        self.client.subscribe(f"{TARGET}/command")
        self.client.subscribe(f"{TARGET}/reset")
        self.client.subscribe(f"{TARGET}/cancel")
        self.client.subscribe(f"{TARGET}/pos")

    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/command":
            command = message.payload.decode("utf-8")
            if command == '?':
                self.write(command)
            else:
                print("COMMAND:", command)
                self.write(command.strip() + "\n")
        elif message.topic == f"{TARGET}/reset":
            if message.payload.decode("utf-8") == "hard":
                self.reset()
            else:
                self.soft_reset()
        elif message.topic == f"{TARGET}/cancel":
            print("cancel")
            self.serialport.write(bytes([0x85]))
            
    def soft_reset(self):
        print("soft reset")
        self.serialport.write(b"\x18") # Ctrl-X

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
    while True:
        s.readline()

if __name__ == "__main__":
    main()
