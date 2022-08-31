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

IMAGEZMQ='raspberrypi'
PORT=5000
PIXEL_SCALE=0.0007 * 2
TARGET="raspberrypi"
XY_STEP_SIZE=100
XY_FEED=100

Z_STEP_SIZE=15
Z_FEED=1

WIDTH=800
HEIGHT=600

class ImageZMQCameraReader(QtCore.QThread):
    imageSignal = QtCore.pyqtSignal(np.ndarray)
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
                        

            self.imageSignal.emit(image_data)
def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2

class MainWindow(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()

        self.state = "None"
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.installEventFilter(self)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi"
        self.client.connectToHost()
        self.client.stateChanged.connect(self.on_stateChanged)
        self.client.messageSignal.connect(self.on_messageSignal)
    
        self.pixmap = None
       

        pen = QtGui.QPen()
        pen.setWidth(20)
        color = QtGui.QColor(255, 0, 0)
        color.setAlpha(1)

        brush = QtGui.QBrush(color)
        #self.currentRect = self.scene.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        #self.currentRect.setZValue(3)

        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)

        self.grid = []
        self.currentPixmap = None
        self.currentPosition = None

        pen = QtGui.QPen(QtGui.QColor(127,127,5))
        pen.setWidth(40)
        color = QtGui.QColor(0, 0, 255)
        color.setAlpha(1)
        brush = QtGui.QBrush(color)
        path = QtGui.QPainterPath()
        self.pathItem = self.scene.addPath(path, pen=pen, brush=brush)
        self.pathItem.setZValue(5)

    def drawForeground(self, p, rect):
        if self.currentPosition is not None:
            p.save()
            p.resetTransform()
            
            
            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            p.setPen(pen)        

            font = QtGui.QFont()
            font.setFamily('Times')
            font.setBold(True)
            font.setPointSize(24)
            p.setFont(font)

            p.drawText(0, 50, self.state)
            p.drawText(0, 100, "X%8.3fmm" % self.currentPosition[0])
            p.drawText(0, 150, "Y%8.3fmm" % self.currentPosition[1])
            p.drawText(0, 200, "Z%8.3fmm" % self.currentPosition[2])

            p.restore()


    def mouseReleaseEvent(self, event):
        br = self.scene.selectionArea().boundingRect()
        

        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(20)
        color = QtGui.QColor(0, 0, 0)
        brush = QtGui.QBrush(color)
        x = br.topLeft().x()
        y = br.topLeft().y()
        width = br.width()
        height = br.height()
        rect = self.scene.addRect(x, y, width, height, pen=pen, brush=brush)
        rect.setZValue(1)
        rect.setOpacity(0.25)

        x_min = br.topLeft().x()* PIXEL_SCALE
        y_min =  -br.bottomRight().y()* PIXEL_SCALE
        x_max = br.bottomRight().x()* PIXEL_SCALE
        y_max =  -br.topLeft().y()* PIXEL_SCALE

        fov = 600 * PIXEL_SCALE
        if (x_max - x_min < fov and y_max - y_min < fov):
            print("Immediate move:")
            cmd = f"$J=G90 G21 X{x_min:.3f} Y{y_min:.3f} F{XY_FEED:.3f}"
            self.client.publish(f"{TARGET}/command", cmd)
        else:
            self.grid = []
            gx = x_min
            gy = y_min
            forward = True

            # self.grid.append("$HX")
            # self.grid.append("$HY")

            self.grid.append(f"$J=G90 G21 X{x_min:.3f} Y{y_min:.3f} F{XY_FEED:.3f}")
            while gy <= y_max:
                if forward:
                    self.grid.append(f"$J=G90 G21 X{x_max:.3f} Y{gy:.3f} F{XY_FEED:.3f}")
                else:
                    self.grid.append(f"$J=G90 G21 X{x_min:.3f} Y{gy:.3f} F{XY_FEED:.3f}")
                #self.grid.append("$HX")
                forward = not forward
                gy += fov

                self.grid.append(f"$J=G90 G21 Y{gy:.3f} F{XY_FEED:.3f}")
            self.grid.append(f"$J=G90 G21 X{x_max:.3f} Y{gy:.3f} F{XY_FEED:.3f}")

            print(self.grid)
            cmd = self.grid.pop(0)
            self.client.publish(f"{TARGET}/command", cmd)

        super().mouseReleaseEvent(event)

    def imageTo(self, draw_data):
        if self.state == "Jog" or self.state == "Idle":
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
                
            self.currentPixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
            if self.pixmap:
                self.pixmap.setPixmap(self.currentPixmap)
                ci = self.pixmap.collidingItems()
                # Get the qpainterpath corresponding to the current image location, minus any overlapping images
                qp = QtGui.QPainterPath()
                qp.addRect(self.pixmap.sceneBoundingRect())
                qp2 = QtGui.QPainterPath()
                for item in ci:
                    if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                        qp2.addRect(item.sceneBoundingRect())

                qp3 = qp.subtracted(qp2)
                p = qp3.toFillPolygon()
                a = calculate_area(p)
                self.pathItem.setPath(qp3)

                # for i in range(self.path.elementCount()):
                #     print(self.path.elementAt(i))
                if a > 350000:# and [item for item in ci if isinstance(item, QtWidgets.QGraphicsPixmapItem)] == []:
                    self.addPixmap()
        else:
            print("Skip because not jogging or idle")

    def addPixmap(self):
        if self.currentPosition and self.currentPixmap:
            pm = self.scene.addPixmap(self.currentPixmap)
            #pm.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
            #pm.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)
            pos = self.currentPosition
            pm.setPos(pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE)
            pm.setZValue(2)
            #pm.setOpacity(0.5)
            self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    # def collide(self):
    #     items = pm.collidingItems()
        
    #     #items = self.items()
    #     #print("Intersections:", items)
    #     for item in items:
    #         # compute PCC
    #         if isinstance(item, QtWidgets.QGraphicsPixmapItem):
    #             i = item.pixmap().toImage()
    #             reference = i.convertToFormat(QtGui.QImage.Format.Format_RGB888).bits()
    #             height = i.height()
    #             width = i.width()
    #             reference.setsize(height * width * 3)
    #             rn = np.frombuffer(reference, np.uint8).reshape(width, height, 3)
    #             #i2 = pm.pixmap().toImage()
    #             #height = i2.height()
    #             #width = i2.width()
    #             #moving = i2.convertToFormat(QtGui.QImage.Format.Format_RGB888).constBits()
    #             #moving.setsize(height * width * 3)
    #             #rm = np.frombuffer(moving, np.uint8).reshape((width, height, 3))
    #             print(rn[0][0])
    #             #print(phase_cross_correlation(rn, rm))

    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if not event.isAutoRepeat():
                key = event.key()    
                type_ = event.type()

                if key == QtCore.Qt.Key_A and type_ == QtCore.QEvent.KeyPress:
                    self.addPixmap()
                    
                    

                elif key == QtCore.Qt.Key_C and type_ == QtCore.QEvent.KeyPress:
                    self.client.publish(f"{TARGET}/cancel", "")

                elif type_ == QtCore.QEvent.KeyRelease and key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Plus, QtCore.Qt.Key_Minus):
                    self.client.publish(f"{TARGET}/cancel", "")

                if self.state == "Idle":
                    if key == QtCore.Qt.Key_Left and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 X-{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                    elif key == QtCore.Qt.Key_Right and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 X{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                    elif key == QtCore.Qt.Key_Up and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 Y{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                    elif key == QtCore.Qt.Key_Down and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 Y-{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                    elif key == QtCore.Qt.Key_Plus and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                    elif key == QtCore.Qt.Key_Minus and type_ == QtCore.QEvent.KeyPress:
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
                #self.currentRect.setPos(pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE)
            if self.state == "Jog" or self.state == "Idle":
                if self.currentPixmap:
                    if not self.pixmap:
                        self.pixmap = self.scene.addPixmap(self.currentPixmap)
                    else:
                        self.pixmap.setPixmap(self.currentPixmap)
                        self.pixmap.setPos(pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE)
                self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
            else:
                print("Not saving image because not in jog or idle")
        elif topic == f'{TARGET}/state':
            if self.state != 'Idle' and payload == 'Idle':
                # should take photo with *previous stage position* here
                # get qimage from pixmap
                # create filename w/ previous stage position
                # save
                print("Machine went idle", self.grid)
                if self.grid != []:
                    cmd = self.grid.pop(0)
                    print("send", cmd)
                    self.client.publish(f"{TARGET}/command", cmd)

            self.state = payload

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
