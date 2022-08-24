import numpy as np
import json
import os
import traceback
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets, QtSvg
import simplejpeg
import imagezmq
from mqtt_qobject import MqttClient

IMAGEZMQ='192.168.1.152'
PORT=5000
PIXEL_SCALE=0.001
TARGET="dekscope"
XY_STEP_SIZE=100
XY_FEED=50


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

class MainWindow(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.installEventFilter(self)


        self.client = MqttClient(self)
        self.client.hostname = "dekscope.local"
        self.client.connectToHost()
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)
    
        
        pixmap = QtGui.QPixmap(1600, 1200)
        pixmap.fill(QtCore.Qt.white)
        self.pixmap = self.scene.addPixmap(pixmap)
        self.pixmap.setZValue(2)
        self.pixmap.setOpacity(0.5)

        pen = QtGui.QPen(QtCore.Qt.red)
        brush = QtGui.QBrush(QtCore.Qt.red)
        self.origin = self.scene.addRect(790, 590, 20, 20, pen=pen, brush=brush)
        self.origin.setZValue(3)

        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)

    def imageTo(self, draw_data):
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.pixmap.setPixmap(pixmap)
        self.currentPixmap = pixmap

    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if not event.isAutoRepeat():
                key = event.key()    

                if key == QtCore.Qt.Key_A:
                    pm = self.scene.addPixmap(self.currentPixmap)
                    pos = self.currentPosition
                    pm.setPos(-pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
                    pm.setZValue(1)
                    pm.setOpacity(0.5)

                    self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
                elif key == QtCore.Qt.Key_Left:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel", "")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel", "")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Right:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel", "")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel", "")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Up:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel", "")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel", "")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Down:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel", "")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel", "")
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Plus:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel", "")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel", "")
                        cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                elif key == QtCore.Qt.Key_Minus:
                    if event.type() == QtCore.QEvent.KeyRelease:
                        self.client.publish(f"{TARGET}/cancel", "")
                    elif event.type() == QtCore.QEvent.KeyPress:
                        self.client.publish(f"{TARGET}/cancel", "")
                        cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
        return super().eventFilter(widget, event)
             
    @QtCore.pyqtSlot(int)
    def on_stateChanged(self, state):
        if state == MqttClient.Connected:
            self.client.subscribe(f"{TARGET}/state")
            self.client.subscribe(f"{TARGET}/m_pos")

    @QtCore.pyqtSlot(str, str)
    def on_messageSignal(self, topic, payload):
        if topic == f'{TARGET}/m_pos':
            pos = json.loads(payload)
            self.currentPosition = pos
            self.pixmap.setPos(-pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
            self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        elif topic == f'{TARGET}/state':
            print("STATUS:", payload)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)
    def notify(self, obj, event):
        try:
            return QtWidgets.QApplication.notify(self, obj, event)
        except Exception:
            print(traceback.format_exception(*sys.exc_info()))
            return False
        
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    app.exec_()
