from math import degrees
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
pcutoff=0.5
pixel_to_mm = 0.00005
TARGET=sys.argv[1]
MQTT_SERVER="gork.local"
IMAGEZMQ='gork.local'
PORT=sys.argv[2]
XY_FEED=25

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
                        
            # gray = cv2.cvtColor(image_data,cv2.COLOR_RGB2GRAY)
            # edges = cv2.Canny(gray,50,150,apertureSize = 3)
            # #image_data = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)

            # lines = cv2.HoughLines(edges,1,np.pi/720,200)\
            
            # if lines is not None:
            #     angles = []
            #     for line in lines:
            #         for rho,theta in line:
            #             if (abs(theta) < 0.3):
            #                 angles.append(theta)
            #                 a = np.cos(theta)
            #                 b = np.sin(theta)
            #                 x0 = a*rho
            #                 y0 = b*rho
            #                 x1 = int(x0 + 1000*(-b))
            #                 y1 = int(y0 + 1000*(a))
            #                 x2 = int(x0 - 1000*(-b))
            #                 y2 = int(y0 - 1000*(a))

            #                 cv2.line(image_data,(x1,y1),(x2,y2),(0,0,255),2)
            #     print(degrees(mean(angles)))

            self.imageSignal.emit(image_data)

class Window(QtWidgets.QLabel):

    def __init__(self):
        super(Window, self).__init__()

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
    
            
    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/m_pos":
            self.m_pos = eval(message.payload)
        elif message.topic == f"{TARGET}/inference":
            print("got results", message.payload)
            self.results = json.loads(message.payload)

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True
        self.client.subscribe(f"{TARGET}/m_pos")
        self.client.subscribe(f"{TARGET}/inference")

    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
        #self.timer.stop()


    def mousePressEvent(self, event):
        # Compute delta from c_pos to middle of window, then scale by pixel size
        s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
        cursor_offset = QtCore.QPointF(event.pos()-s_pos)*pixel_to_mm*5
        cmd = "$J=G91  G21 X%.3f Y%.3f F%.3f"% (-cursor_offset.x(), -cursor_offset.y(), XY_FEED)
        self.client.publish(f"{TARGET}/command", cmd)

    def imageTo(self, image): 
        image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
        #(self.m_pos)
        
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

            p.drawText(0, 50, "X%8.3fmm" % self.m_pos[0])
            p.drawText(0, 100, "Y%8.3fmm" % self.m_pos[1])
            p.drawText(0, 150, "Z%8.3fmm" % self.m_pos[2])
            p.end()

        if self.results:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            pen1 = QtGui.QPen(QtCore.Qt.black)
            pen1.setWidth(2)
                
            
            pen2 = QtGui.QPen(QtCore.Qt.blue)
            pen.setWidth(2)

            for result in self.results['results']:
                prediction_score = result[0]
                label = result[1]
                box = result[2]
                p.setPen(pen1)
                box = QtCore.QRectF(QtCore.QPointF(*box[0]), QtCore.QPointF(*box[1]))
                p.drawRect(box)
                p.setPen(pen2)
                p.drawText(box.bottomRight(), "%5.2f %s" % (prediction_score, label))
                image_center = QtCore.QPointF(image.width()/2, image.height()/2)
                if label == 'tardigrade' and prediction_score > 0.9:
                    p.drawLine(image_center, box.center())
                   

            self.results = None
            p.end()

        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.resize(pixmap.size().width(), pixmap.size().height())
        self.setPixmap(pixmap)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()#FullScreen()

    app.exec_()

