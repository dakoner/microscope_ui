import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import paho.mqtt.client as mqtt
import simplejpeg
import imagezmq

XY_STEP_SIZE=0.1
Z_STEP_SIZE=0.1
TARGET="microscope"
MQTT_SERVER="gork.local"
IMAGEZMQ='DESKTOP-H3TSLD0.local'

class ImageZMQCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(QtGui.QImage)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = "tcp://{}:{}".format(IMAGEZMQ, 5555)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

    def run(self):         
        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='GRAY')
            image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_Indexed8)
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
        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.image_widget.setPixmap(pixmap)

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()#FullScreen()

    app.exec_()
