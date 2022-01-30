import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
from simple_pyspin import Camera
import paho.mqtt.client as mqtt
import cv2
import imutils
import simplejpeg
import imagezmq

XY_STEP_SIZE=0.1
Z_STEP_SIZE=0.1
TARGET="inspectionscope"
MQTT_SERVER="gork.local"

class ImageZMQCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(QtGui.QImage)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        self.image_hub = imagezmq.ImageHub()

    def run(self):         
        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
            self.signal.emit(image)
            self.image_hub.send_reply(b'OK')

class PySpinCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(QtGui.QImage)
    def __init__(self):
        super(PySpinCameraReader, self).__init__()
        self.cam = Camera()
        self.cam.init()

    def run(self):         
        self.cam.start()
        while True:
            img = self.cam.get_array()
            image = QtGui.QImage(img, self.cam.Width, self.cam.Height, QtGui.QImage.Format_Grayscale8)
            self.signal.emit(image)


class Cv2CameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(QtGui.QImage)
    def __init__(self):
        super(Cv2CameraReader, self).__init__()
        self.cam = cv2.VideoCapture(0)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)
        self.width = self.cam.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
    def run(self):
        while True:
            ret, img = self.cam.read()
            if ret:
                image = QtGui.QImage(img.data, self.width, self.height, QtGui.QImage.Format_RGB888)
                self.signal.emit(image)



class PiCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(QtGui.QImage)
    def __init__(self):
        super(PiCameraReader, self).__init__()
        self.picam = imutils.VideoStream(usePiCamera=True).start()
        self.width = self.picam.camera.resolution[0]
        import pdb; pdb.set_trace()

    def run(self):
        while True:
            image = self.picam.read()
            image = QtGui.QImage(image, self.width, self.height, QtGui.QImage.Format_RGB888)
            self.signal.emit(image)

class Window(QtWidgets.QWidget):

    def __init__(self):
        super(Window, self).__init__()

        self.central_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.central_layout)
        self.image_widget = QtWidgets.QLabel(self)
        self.central_layout.addWidget(self.image_widget)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.setFocus()

        #self.camera = Cv2CameraReader()
        #self.camera = PySpinCameraReader()
        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.signal.connect(self.imageTo)

        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.connect_async(MQTT_SERVER)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
    def on_disconnect(self, client, userdata, flags, rc):
        print("disconnected")

    def keyPressEvent(self, event):
        cmd = None
        if event.key() == QtCore.Qt.Key_Q:
            cmd = "$J=G91 F100 Z-%f" % Z_STEP_SIZE
        elif event.key() == QtCore.Qt.Key_Z:
            cmd = "$J=G91 F100 Z%f" % Z_STEP_SIZE
        elif event.key() == QtCore.Qt.Key_A:
            cmd = "$J=G91 F100 Y-%f" % XY_STEP_SIZE
        elif event.key() == QtCore.Qt.Key_D:
            cmd = "$J=G91 F100 Y%f" % XY_STEP_SIZE
        elif event.key() == QtCore.Qt.Key_W:
            cmd = "$J=G91 F100 X%f" % XY_STEP_SIZE
        elif event.key() == QtCore.Qt.Key_S:
            cmd = "$J=G91 F100 X-%f" % XY_STEP_SIZE
        # elif event.key() == QtCore.Qt.Key_X:
        #     QtWidgets.qApp.quit()
        if cmd:
            self.client.publish(f"{TARGET}/command", cmd)


    def imageTo(self, image): 
        image = QtGui.QPixmap.fromImage(image).scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.image_widget.setPixmap(image)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()#FullScreen()

    app.exec_()
