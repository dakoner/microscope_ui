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

def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2

class MainWindow(QtWidgets.QGraphicsView):
    def __del__(self):
        print("done")
        self.camera.quit()

    def __init__(self):
        super().__init__()

        self.state = "None"
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self.scene)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.installEventFilter(self)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.scene.setSceneRect(0, -35000, 35000, 35000)
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)


        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi"
        self.client.connectToHost()
        
    
        self.pixmap = self.scene.addPixmap(QtGui.QPixmap())
       

        pen = QtGui.QPen()
        pen.setWidth(20)
        color = QtGui.QColor(255, 0, 0)
        color.setAlpha(1)
        brush = QtGui.QBrush(color)
        self.currentRect = self.scene.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(3)

        #self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)

        self.grid = []
        self.currentPosition = None

        # pen = QtGui.QPen(QtGui.QColor(127,127,5))
        # pen.setWidth(40)
        # color = QtGui.QColor(0, 0, 255)
        # color.setAlpha(1)
        # brush = QtGui.QBrush(color)
        # path = QtGui.QPainterPath()
        # self.pathItem = self.scene.addPath(path, pen=pen, brush=brush)
        # self.pathItem.setZValue(5)


        self.tile_config = open("movie/TileConfiguration.txt", "w")
        self.tile_config.write("dim=2\n")
        self.tile_config.flush()
        self.counter = 0

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
            font.setPointSize(12)
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

            #self.grid.append("$H")
            # self.grid.append("$HY")
            #self.grid.append("$HY")

            while gy <= y_max:
                while gx <= x_max:
                    self.grid.append(f"$J=G90 G21 X{gx:.3f} Y{gy:.3f} F{XY_FEED:.3f}")
                    gx += fov/2
                gx = x_min
                gy += fov/2

            cmd = self.grid.pop(0)
            self.client.publish(f"{TARGET}/command", cmd)

        super().mouseReleaseEvent(event)

    def imageTo(self, message, draw_data):
        m = json.loads(message)
        print(m)
        #print("message:", m['state'], m['m_pos'])
        state = m['state']
        
        went_idle=False
        if self.state != 'Idle' and state == 'Idle':
            went_idle=True
        self.state = state
        
        self.currentPosition = m['m_pos']

        if self.state != 'Home':
            pos = self.currentPosition
            self.currentRect.setPos(pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE)
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)    
            currentPixmap = QtGui.QPixmap.fromImage(image)
            self.pixmap.setPixmap(currentPixmap)
            self.pixmap.setPos(pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE)

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
            #self.pathItem.setPath(qp3)

            scale_pos = pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE
            if a > 240000:# and [item for item in ci if isinstance(item, QtWidgets.QGraphicsPixmapItem)] == []:
                pm = self.scene.addPixmap(currentPixmap)
                pm.setPos(*scale_pos)
                pm.setZValue(2)

                #pm.setOpacity(0.5)
            if went_idle:
                fname = "image.%05d.png" % self.counter
                image.convertToFormat(QtGui.QImage.Format_Grayscale8).save("movie/" + fname)
                self.tile_config.write(f"{fname}; ; ({scale_pos[0]}, {scale_pos[1]})\n")
                self.tile_config.flush()
                self.counter += 1
        self.scene.update()

        if went_idle:
            print("Machine went idle", self.grid)
            if self.grid != []:
                cmd = self.grid.pop(0)
                self.client.publish(f"{TARGET}/command", cmd)
        
    def keyPressEvent(self, *args):
        return None

    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            if not event.isAutoRepeat():
                key = event.key()    
                type_ = event.type()

                if key == QtCore.Qt.Key_C and type_ == QtCore.QEvent.KeyPress:
                    self.client.publish(f"{TARGET}/cancel", "")
                    return True

                elif type_ == QtCore.QEvent.KeyRelease and key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Plus, QtCore.Qt.Key_Minus):
                    self.client.publish(f"{TARGET}/cancel", "")
                    return True

                elif self.state == "Idle":
                    if key == QtCore.Qt.Key_Left and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 X-{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                            return True
                    elif key == QtCore.Qt.Key_Right and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 X{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                            return True
                    elif key == QtCore.Qt.Key_Up and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 Y{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                            return True
                    elif key == QtCore.Qt.Key_Down and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 Y-{XY_STEP_SIZE:.3f} F{XY_FEED:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                            return True
                    elif key == QtCore.Qt.Key_Plus and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                            return True
                    elif key == QtCore.Qt.Key_Minus and type_ == QtCore.QEvent.KeyPress:
                            cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                            self.client.publish(f"{TARGET}/command", cmd)
                            return True

        return super().eventFilter(widget, event)
        #return True

     
if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    app.exec_()
