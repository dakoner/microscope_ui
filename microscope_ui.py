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
MQTT_SERVER="dekscope.local"
IMAGEZMQ='dekscope.local'
TARGET=sys.argv[1]
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
                        

            self.imageSignal.emit(image_data)

class ControlWindow(QtWidgets.QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.slider_one = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_one.setMinimum(0)
        self.slider_one.setMaximum(200)
        self.slider_one.valueChanged[int].connect(self.slider_one_changed)
        self.slider_one.setValue(self.window.one)

        self.slider_two = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_two.setMinimum(0)
        self.slider_two.setMaximum(200)
        self.slider_two.valueChanged[int].connect(self.slider_two_changed)
        self.slider_two.setValue(self.window.two)


        # self.rho = 1 # double
        # self.theta = np.pi/2 # double
        # self.threshold = 1 # int
        # self.minLineLength = 25 # double
        # self.maxLineGap = 25 # double

        self.slider_rho = QtWidgets.QDoubleSpinBox(self)
        self.slider_rho.setMinimum(0)
        self.slider_rho.setMaximum(10)
        self.slider_rho.setSingleStep(0.1)
        self.slider_rho.valueChanged[float].connect(self.slider_rho_changed)
        self.slider_rho.setValue(self.window.rho)
        
        self.slider_threshold = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider_threshold.setMinimum(0)
        self.slider_threshold.setMaximum(200)
        self.slider_threshold.valueChanged[int].connect(self.slider_threshold_changed)
        self.slider_threshold.setValue(self.window.threshold)
    
        self.slider_minLineLength = QtWidgets.QDoubleSpinBox(self)
        self.slider_minLineLength.setMinimum(0)
        self.slider_minLineLength.setMaximum(100)
        self.slider_minLineLength.setSingleStep(1)
        self.slider_minLineLength.valueChanged[float].connect(self.slider_minLineLength_changed)
        self.slider_minLineLength.setValue(self.window.minLineLength)
        
        self.slider_maxLineGap = QtWidgets.QDoubleSpinBox(self)
        self.slider_maxLineGap.setMinimum(0)
        self.slider_maxLineGap.setMaximum(100)
        self.slider_maxLineGap.setSingleStep(1)
        self.slider_maxLineGap.valueChanged[float].connect(self.slider_maxLineGap_changed)
        self.slider_maxLineGap.setValue(self.window.maxLineGap)

        layout.addWidget(self.slider_one)
        layout.addWidget(self.slider_two)
        layout.addWidget(self.slider_rho)
        layout.addWidget(self.slider_threshold)
        layout.addWidget(self.slider_minLineLength)
        layout.addWidget(self.slider_maxLineGap)

    def slider_one_changed(self, value):
        print("one changed", value)
        self.window.one = value

    def slider_two_changed(self, value):
        print("two changed", value)
        self.window.two = value

    def slider_rho_changed(self, value):
        print("rho changed", value)
        self.window.rho = value

    def slider_threshold_changed(self, value):
        print("threshold changed", value)
        self.window.threshold = value

    def slider_minLineLength_changed(self, value):
        print("minLineLength changed", value)
        self.window.minLineLength = value

    def slider_maxLineGap_changed(self, value):
        print("maxLineGap changed", value)
        self.window.maxLineGap = value

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
        self.one = 50
        self.two = 100

        self.rho = 1 # double
        self.theta = np.pi/2 # double
        self.threshold = 1 # int
        self.minLineLength = 25 # double
        self.maxLineGap = 25 # double

        self.old_image = None 

    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/m_pos":
            self.m_pos = eval(message.payload)
        # elif message.topic == f"{TARGET}/inference":
        #     self.results = json.loads(message.payload)

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

    def get_mask(self, image_data):
        image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(image_data,
                        np.array((0, 0, 0), dtype=np.uint8),
                        np.array((255, 255, 5), dtype=np.uint8))
        mask = cv2.erode(mask, None, iterations=4)
        mask = cv2.dilate(mask, None, iterations=1)
        
        return mask
        

    def find_contours(self, image_data, mask):
        # Find contours and find total area
        cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        area = 0
        gray = cv2.cvtColor(image_data,cv2.COLOR_BGR2GRAY)

        for c in cnts:
            cv2.drawContours(gray,[c], 0, (0,255,0), 2)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def find_lines(self, image_data):
        src = cv2.GaussianBlur(image_data, (3, 3), 0)
        gray = cv2.cvtColor(src,cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray,self.one, self.two, apertureSize = 3)
        #kernel = np.ones((3,3), np.uint8)
        #img_dilation = cv2.dilate(edges, kernel, iterations=1)
        #img_erosion = cv2.erode(img_dilation, kernel, iterations=1)

        lines = cv2.HoughLinesP(edges,self.rho, self.theta,self.threshold, self.minLineLength, self.maxLineGap)
        draw_data = image_data.copy()
        if lines is not None:
            for line in lines:
                for x1, y1, x2, y2 in line:
                    cv2.line(draw_data,(x1,y1),(x2,y2),(0,255,255),2)
        return draw_data #cv2.cvtColor(draw_data, cv2.COLOR_GRAY2BGR)
    
    def sobel(self, image_data):
        scale = 1
        delta = 0
        ddepth = cv2.CV_16S

        src = cv2.GaussianBlur(image_data, (3,3), 0)
        gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(gray, ddepth, 1, 0, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        grad_y = cv2.Sobel(gray, ddepth, 0, 1, ksize=3, scale=scale, delta=delta, borderType=cv2.BORDER_DEFAULT)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        print(np.sqrt(np.sum(abs_grad_x**2 + abs_grad_y**2)))
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
        
        return cv2.cvtColor(grad, cv2.COLOR_GRAY2BGR)

    

    def imageTo(self, image_data): 

        if self.old_image is None:
            self.old_image = image_data
            return



        #image_data = cv2.addWeighted(self.old_image, 0.9, image_data,  0.1, 0)


        #image_data = self.sobel(image_data)
        draw_data = self.find_lines(image_data)
        #draw_data = self.find_contours(image_data, mask)




        # mask = self.get_mask(image_data)
        # image_data = cv2.cvtColor(image_data, cv2.COLOR_HSV2RGB)
        # blue = np.full_like(image_data, (255, 0, 0))
        # draw_data = cv2.bitwise_and(blue, image_data, mask=mask)

        #self.find_contours(image_data, mask)
        #draw_data = self.find_lines(image_data)
        #draw_data = image_data
        self.old_image = image_data
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

            p.drawText(0, 50, "X%8.3fmm" % self.m_pos[0])
            p.drawText(0, 100, "Y%8.3fmm" % self.m_pos[1])
            p.drawText(0, 150, "Z%8.3fmm" % self.m_pos[2])
            p.end()

        # if self.results:
        #     p = QtGui.QPainter()
        
        #     p.begin(image)
        #     p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
        #     p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

        #     pen1 = QtGui.QPen(QtCore.Qt.black)
        #     pen1.setWidth(2)
                
            
        #     pen2 = QtGui.QPen(QtCore.Qt.blue)
        #     pen2.setWidth(2)
        #     first = True
        #     for result in self.results['results']:
        #         prediction_score = result[0]
        #         label = result[1]
        #         box = result[2]
        #         p.setPen(pen1)
        #         box = QtCore.QRectF(QtCore.QPointF(*box[0]), QtCore.QPointF(*box[1]))
        #         p.drawRect(box)
        #         p.setPen(pen2)
        #         p.drawText(box.bottomRight(), "%5.2f %s" % (prediction_score, label))
        #         image_center = QtCore.QPointF(image.width()/2, image.height()/2)
        #         if label == 'tardigrade' and prediction_score == 1.0 and first:
        #             p.drawLine(image_center, box.center())
        #             first = False

        #     self.results = None
        #     p.end()

        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.resize(pixmap.size().width(), pixmap.size().height())
        self.setPixmap(pixmap)



if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    cw = ControlWindow(window)
    window.show()#FullScreen()
    cw.show()

    app.exec_()

