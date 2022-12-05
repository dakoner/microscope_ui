import signal
import math
import numpy as np
from controller.image_zmq_camera_reader import ImageZMQCameraReader
from controller.mqtt_qobject import MqttClient
from config import TARGET, IMAGEZMQ

import time
import sys
import cv2
import imagezmq
import simplejpeg

from PyQt5 import QtCore

            


IMAGEZMQ='microcontroller'
PORT=5000
url = f"tcp://{IMAGEZMQ}:{PORT}"
image_hub = imagezmq.ImageHub(url, REQ_REP=False)


class QApplication(QtCore.QCoreApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)

        
        self.client = MqttClient(self)
        self.client.hostname = "microcontroller"
        self.client.connectToHost()
        self.client.messageSignal.connect(self.on_message)
        self.client.connected.connect(self.on_connect)

        self.camera = ImageZMQCameraReader()
        self.camera.imageChanged.connect(self.imageChanged)
        self.camera.start()

        self.out = None
        self.m_pos = None
        self.m_pos_time = time.time()
        self.state = None

        self.counter = 0
        
    def on_message(self, topic, payload):
        pos = eval(payload)
        self.m_pos = pos
        self.m_pos_time = time.time()

    def on_connect(self):
        print("on_connect", TARGET)
        self.connected = True
        self.client.subscribe(f"{TARGET}/m_pos")

    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
       
    def imageChanged(self, draw_data):
        if self.out is None:
            self.out = cv2.VideoWriter('outpy.mkv',cv2.VideoWriter_fourcc(*'XVID'), 10, (draw_data.shape[1], draw_data.shape[0]), isColor=False)
        t0 = time.time()
        d = draw_data.sum() / math.prod(draw_data.shape)
        if d> 50:
            self.out.write(draw_data)
            self.counter += 1

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    q = QApplication(sys.argv)
    q.exec_()
