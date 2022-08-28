from math import degrees, cos, sin
from statistics import mean
from calendar import c
import os
import cv2
import time
import sys
import signal
from PIL import Image, ImageDraw, ImageFont
from PyQt5 import QtGui, QtCore, QtWidgets
from six import BytesIO
import paho.mqtt.client as mqtt
import simplejpeg
import imagezmq
import numpy as np
import time
import classes
import json
from collections import deque
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt 




pcutoff=0.5
pixel_to_mm = 0.00005
MQTT_SERVER="raspberrypi"
IMAGEZMQ='raspberrypi'
TARGET=sys.argv[1]
PORT=sys.argv[2]
XY_STEP_SIZE=100
XY_FEED=50

Z_STEP_SIZE=15
Z_FEED=1
keys = (QtCore.Qt.Key_0, QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_5, QtCore.Qt.Key_6, QtCore.Qt.Key_7, QtCore.Qt.Key_8, QtCore.Qt.Key_9)
MovementKeys=(QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)
colormap = [QtCore.Qt.red, QtCore.Qt.green, QtCore.Qt.blue, QtCore.Qt.yellow, QtCore.Qt.magenta, QtCore.Qt.black]


counter = 0


fontScale = 1
color = (255, 0, 0)
thickness = 2
font = cv2.FONT_HERSHEY_SIMPLEX

class ImageZMQCameraReader(QtCore.QThread):
    imageSignal = QtCore.pyqtSignal(np.ndarray)
    #predictSignal = QtCore.pyqtSignal(list)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)
    def run(self):         
        name, jpg_buffer = self.image_hub.recv_jpg()
        image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')

        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
                        

            self.imageSignal.emit(image_data)

class ControlWindow(QtWidgets.QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)




class MplWindow(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.figure = Figure(figsize=(1, 1), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.axes = self.figure.add_subplot(111)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.setLayout(self.layout)

class Window(QtWidgets.QLabel):
    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if not event.isAutoRepeat():
                key = event.key()    

                if key == QtCore.Qt.Key_Left:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Right:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Up:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Down:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Plus:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel")
                        cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Minus:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel")
                        cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                        

        return super().eventFilter(widget, event)

    def __init__(self, mpl_window):
        super(Window, self).__init__()

        self.installEventFilter(self)
    
        self.mpl_window = mpl_window

        #self.resize(640,480)
        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)


        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)
        self.client.loop_start()
        self.outstanding = 0

        self.positions = {}
        self.connected = False

        self.m_pos = None
        self.w_pos = None

        self.time = None
        self.state = "Unknown"

        self.results = None
        self.one = 50
        self.two = 100

        self.old_image = None 

        self.queue = deque()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timerExpired)
        self.timer.start(1000)

    def timerExpired(self, *args):
        if self.connected:
            self.client.publish(f"{TARGET}/command", "?")

    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/m_pos":
            self.m_pos = eval(message.payload)
        # elif message.topic == f"{TARGET}/inference":
        #     self.results = json.loads(message.payload)
        elif message.topic == f"{TARGET}/state":
            self.state = message.payload.decode('utf-8')

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True
        self.client.subscribe(f"{TARGET}/m_pos")
        #self.client.subscribe(f"{TARGET}/inference")
        self.client.subscribe(f"{TARGET}/state")

    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False


    def mousePressEvent(self, event):
        # Compute delta from c_pos to middle of window, then scale by pixel size
        s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
        cursor_offset = QtCore.QPointF(event.pos()-s_pos)*pixel_to_mm*30
        cmd = "$J=G91  G21 X%.3f Y%.3f F%.3f"% (-cursor_offset.x(), cursor_offset.y(), XY_FEED)
        self.client.publish(f"{TARGET}/command", cmd)

        


    def imageTo(self, image_data): 
        draw_data = image_data
       
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)

        if self.m_pos is not None:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            #p.drawImage(QtCore.QPoint(), image)

            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            p.setPen(pen)        

            font = QtGui.QFont()
            font.setFamily('Times')
            font.setBold(True)
            font.setPointSize(24)
            p.setFont(font)

            p.drawText(0, 50, self.state)
            p.drawText(0, 100, "X%8.3fmm" % self.m_pos[0])
            p.drawText(0, 150, "Y%8.3fmm" % self.m_pos[1])
            p.drawText(0, 200, "Z%8.3fmm" % self.m_pos[2])
            p.end()



        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.resize(pixmap.size().width(), pixmap.size().height())
        self.setPixmap(pixmap)



if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)

    sc = MplWindow()
    sc.show()
    window = Window(sc)
    

    cw = ControlWindow(window)
    window.show()#FullScreen()
    cw.show()

    app.exec_()

