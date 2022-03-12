import cv2
#import cv2.aruco
import time
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import paho.mqtt.client as mqtt
import simplejpeg
import imagezmq
import numpy as np
#from dlclive import DLCLive

pcutoff=0.5
pixel_to_mm = 0.0003
XY_STEP_SIZE=500
Z_STEP_SIZE=.003
Z_FEED=500
XY_FEED=10000
TARGET="inspectionscope"
MQTT_SERVER="gork.local"
IMAGEZMQ='gork.local'
PORT=5556

keys = (QtCore.Qt.Key_0, QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_5, QtCore.Qt.Key_6, QtCore.Qt.Key_7, QtCore.Qt.Key_8, QtCore.Qt.Key_9)
MovementKeys=(QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)
colormap = [QtCore.Qt.red, QtCore.Qt.green, QtCore.Qt.blue, QtCore.Qt.yellow, QtCore.Qt.magenta, QtCore.Qt.black]

class ImageZMQCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)


        # self.live = DLCLive(
        #     model_path = r"C:\Users\dek\Desktop\tarditrack2-dek-2022-02-18\exported-models\DLC_tarditrack2_resnet_50_iteration-0_shuffle-1",
        #     tf_config=None,
        #     resize=0.5,
        #     cropping=None,
        #     dynamic=(False, 0.5, 10),
        #     display=False,
        #     pcutoff=0.5,
        #     display_radius=3,
        #     display_cmap='bmy',
        # ) 

    def run(self):         
        name, jpg_buffer = self.image_hub.recv_jpg()
        image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
        #poses = self.live.init_inference(image)

        #aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)
        #parameters =  cv2.aruco.DetectorParameters_create()
        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            #corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, aruco_dict, parameters=parameters)
            #cv2.aruco.drawDetectedMarkers(image, corners, ids)
            
            # gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            # kernel_size = 25
            # blur_gray = cv2.GaussianBlur(gray,(kernel_size, kernel_size),0)
            # low_threshold = 50
            # high_threshold = 150
            # edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
            # rho = 1  # distance resolution in pixels of the Hough grid
            # theta = np.pi / 180  # angular resolution in radians of the Hough grid
            # threshold = 15  # minimum number of votes (intersections in Hough grid cell)
            # min_line_length = 50  # minimum number of pixels making up a line
            # max_line_gap = 20  # maximum gap in pixels between connectable line segments
            # line_image = np.copy(image) * 0  # creating a blank to draw lines on

            # # Run Hough on edge detected image
            # # Output "lines" is an array containing endpoints of detected line segments
            # lines = cv2.HoughLinesP(edges, rho, theta, threshold, np.array([]),
            #                     min_line_length, max_line_gap)
            # if lines is not None:
            #     for line in lines:
            #         for x1,y1,x2,y2 in line:
            #             cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),5)
            # lines_edges = cv2.addWeighted(image, 0.8, line_image, 1, 0)

            #poses = self.live.get_pose(image)
            #self.signal.emit(image, poses)
            self.signal.emit(image, np.zeros((5,3)))

class Window(QtWidgets.QLabel):

    def __init__(self):
        super(Window, self).__init__()

        #self.resize(640,480)
        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.signal.connect(self.imageTo)

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
        self.tracking = False
        self.state = "Unknown"


    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/m_pos":
            self.m_pos = eval(message.payload)

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True
        self.client.subscribe(f"{TARGET}/output")
        self.client.subscribe(f"{TARGET}/command")
        self.client.subscribe(f"{TARGET}/status")
        self.client.subscribe(f"{TARGET}/m_pos")


    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
        self.timer.stop()


    def mousePressEvent(self, event):
        # Compute delta from c_pos to middle of window, then scale by pixel size
        s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
        cursor_offset = QtCore.QPointF(event.pos()-s_pos)*pixel_to_mm
        cmd = "$J=G91 G0  X%.3f Y%.3f F%.3f"% (cursor_offset.y(), cursor_offset.x(), XY_FEED)
        self.client.publish(f"{TARGET}/command", cmd)

    def imageTo(self, image, this_pose): 
        image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
        #(self.m_pos)
        if self.m_pos is not None:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            p.drawImage(QtCore.QPoint(), image)

            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            p.setPen(pen)        

            font = QtGui.QFont()
            font.setFamily('Times')
            font.setBold(True)
            font.setPointSize(24)
            p.setFont(font)

            # c_pos = self.mapFromGlobal(QtGui.QCursor().pos())
            # # Compute delta from c_pos to middle of window, then scale by pixel size
            # s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
            p.drawText(750, 50, "X%8.3fmm" % self.m_pos[0])
            p.drawText(750, 100, "Y%8.3fmm" % self.m_pos[1])
            p.drawText(750, 150, "Z%8.3fmm" % self.m_pos[2])
            # if self.tracking and this_pose[1,2] > pcutoff:
            #     x = int(this_pose[1, 0])
            #     y = int(this_pose[1, 1])
            #     pos = QtCore.QPoint(x, y)
            #     s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
            #     offset = QtCore.QPointF(pos-s_pos)*pixel_to_mm
            #     cmd = "$J=G91 G0 F%.3f X%.3f Y%.3f"% (XY_FEED, offset.y(), offset.x())
            #     t = time.time()
            #     if self.time is None or t - self.time > 1.5:
            #         self.client.publish(f"{TARGET}/command", cmd)
            #         self.time = t

            # for j in range(this_pose.shape[0]):
            #     if this_pose[j, 2] > pcutoff:
            #         x = int(this_pose[j, 0])
            #         y = int(this_pose[j, 1])
                    
            #         p.setBrush(colormap[j])
            #         p.setPen(QtGui.QPen(colormap[j]))   
            #         p.drawEllipse(x, y, 5, 5 )
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
