import numpy as np
import json
import os
import traceback
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import simplejpeg
import imagezmq
from mqtt_qobject import MqttClient

IMAGEZMQ='raspberrypi.local'
PORT=5000
PIXEL_SCALE=0.0007 * 2
TARGET="raspberrypi"
XY_STEP_SIZE=100
XY_FEED=50

Z_STEP_SIZE=15
Z_FEED=1

WIDTH=800
HEIGHT=600

class ImageZMQCameraReader(QtCore.QThread):
    imageSignal = QtCore.pyqtSignal(str, np.ndarray)
    #predictSignal = QtCore.pyqtSignal(list)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

    def run(self):         
        message, jpg_buffer = self.image_hub.recv_jpg()
        image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')

        while True:
            message, jpg_buffer = self.image_hub.recv_jpg()
            #print("message:", message)
            image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            self.imageSignal.emit(message, image_data)

class MainWindow(QtWidgets.QLabel):
   
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)


class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.state = "None"
        self.grid = []
        self.currentPosition = None

        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi.local"
        self.client.connectToHost()

        self.widget = MainWindow(app=self)
        self.widget.show()
        
        
        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)


    def imageTo(self, message, draw_data):
        m = json.loads(message)
        print(m)
        #print("message:", m['state'], m['m_pos'])
        state = m['state']
        
        self.currentPosition = m['m_pos']

        pos = self.currentPosition
        print(pos)
        scale_pos = pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE
        print(draw_data.shape)
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)    
        currentPixmap = QtGui.QPixmap.fromImage(image)
        self.widget.setPixmap(currentPixmap)
        self.widget.adjustSize()

    

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
   
    app.exec_()
