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
from PyQt5.uic import loadUi

IMAGEZMQ='raspberrypi.local'
PORT=5000
PIXEL_SCALE=0.00141509367
TARGET="raspberrypi"
XY_STEP_SIZE=0.1
XY_FEED=100

Z_STEP_SIZE=0.01
Z_FEED=25

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
   
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)

        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)

    def keyPressEvent(self, *args):
        return None

    # def drawForeground(self, p, rect):
    #     if self.app.currentPosition is not None:
    #         p.save()
    #         p.resetTransform()
            
            
    #         pen = QtGui.QPen(QtCore.Qt.red)
    #         pen.setWidth(2)
    #         p.setPen(pen)        

    #         font = QtGui.QFont()
    #         font.setFamily('Times')
    #         font.setBold(True)
    #         font.setPointSize(12)
    #         p.setFont(font)

    #         p.drawText(0, 50, self.app.state)
    #         p.drawText(0, 100, "X%8.3fmm" % self.app.currentPosition[0])
    #         p.drawText(0, 150, "Y%8.3fmm" % self.app.currentPosition[1])
    #         p.drawText(0, 200, "Z%8.3fmm" % self.app.currentPosition[2])

    #         p.restore()



class ZoomWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
    
    def keyPressEvent(self, *args):
        return None

class DRO(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("dro.ui", self)

class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSceneRect(0, -35000, 35000, 35000)
    #     self.installEventFilter(self)


    # def eventFilter(self, widget, event):
    #     print("scene event filter", widget, event)
    #     return super().eventFilter(widget, event)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dro = DRO()
        self.dro.show()

        self.state = "None"
        self.grid = []
        self.currentPosition = None

        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi.local"
        self.client.connectToHost()

        self.widget = MainWindow(app=self)
        self.widget.show()
        

        self.scene = Scene(self)

        self.widget.setScene(self.scene)
        self.widget.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
 
    
        self.pixmap = self.scene.addPixmap(QtGui.QPixmap())
        self.pixmap.setZValue(4)

        pen = QtGui.QPen()
        pen.setWidth(20)
        color = QtGui.QColor(255, 0, 0)
        color.setAlpha(1)
        brush = QtGui.QBrush(color)
        self.currentRect = self.scene.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(3)

        
        # self.widget2 = ZoomWindow()
        # self.widget2.show()
        # self.widget2.setScene(self.scene)

        self.widget3 = QtWidgets.QLabel()
        self.widget3.show()
        
        # self.widget2.fitInView(self.scene.sceneRect())
        # self.widget2.scale(10,10)

        # self.widget2.centerOn(self.currentRect)
        # self.widget2.fitInView(self.currentRect, QtCore.Qt.KeepAspectRatio)
        


        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)
        self.currentImage = None

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

        self.installEventFilter(self)

    # def notify(self, obj, event):
    #     try:
    #         return QtWidgets.QApplication.notify(self, obj, event)
    #     except Exception:
    #         print(traceback.format_exception(*sys.exc_info()))
    #         return False


    def imageTo(self, message, draw_data):
        m = json.loads(message)
        #print(m)
        #print("message:", m['state'], m['m_pos'])
        state = m['state']
        if self.state != state:
            print("Change in state:", self.state, state)
        went_idle=False
        if self.state != 'Idle' and state == 'Idle':
            went_idle=True
        self.state = state
        
        self.currentPosition = m['m_pos']

        if self.state != 'Home':
            pos = self.currentPosition
            self.scale_pos = pos[0]/PIXEL_SCALE, -pos[1]/PIXEL_SCALE
            self.dro.x_value.display(pos[0])
            self.dro.y_value.display(pos[1])
            self.dro.z_value.display(pos[2])
            self.dro.state_value.setText(self.state)
            self.currentRect.setPos(*self.scale_pos)
              
            # self.widget2.centerOn(self.currentRect)
            # self.widget2.fitInView(self.currentRect, QtCore.Qt.KeepAspectRatio)

            self.currentImage = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)    
            self.currentPixmap = QtGui.QPixmap.fromImage(self.currentImage)
            self.pixmap.setPixmap(self.currentPixmap)
            self.pixmap.setPos(*self.scale_pos)

            self.widget3.setPixmap(self.currentPixmap)
            self.widget3.adjustSize()

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

            if a > 240000:# and [item for item in ci if isinstance(item, QtWidgets.QGraphicsPixmapItem)] == []:
                pm = self.scene.addPixmap(self.currentPixmap)
                pm.setPos(*self.scale_pos)
                pm.setZValue(2)

                #pm.setOpacity(0.5)
            if went_idle and len(self.grid):
                fname = "image.%05d.png" % self.counter
                if self.currentImage is not None:
                    self.currentImage.convertToFormat(QtGui.QImage.Format_Grayscale8).save("movie/" + fname)
                    self.tile_config.write(f"{fname}; ; ({self.scale_pos[1]}, {self.scale_pos[0]})\n")
                    self.tile_config.flush()
                    self.counter += 1
        self.scene.update()

        if went_idle:
            print("Machine went idle")
            if self.grid != []:
                cmd = self.grid.pop(0)
                self.client.publish(f"{TARGET}/command", cmd)
        


    def generateGrid(self, start_event, end_event):
        br = self.scene.itemsBoundingRect()
        print("bounding rect", br)
        print("event", start_event, end_event)

        sp = self.widget.mapToScene(start_event)
        ep = self.widget.mapToScene(end_event)
        x = sp.x()
        y = sp.y()
        width = ep.x()-x
        height = ep.y()-y
        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(20)
        color = QtGui.QColor(0, 0, 0)
        brush = QtGui.QBrush(color)
        #x = br.topLeft().x()
        #y = br.topLeft().y()
        #width = br.width()
        #height = br.height()
        rect = self.scene.addRect(x, y, width, height, pen=pen, brush=brush)
        rect.setZValue(6)
        rect.setOpacity(0.25)

        # x_min = br.topLeft().x()* PIXEL_SCALE
        # y_min =  -br.bottomRight().y()* PIXEL_SCALE
        # x_max = br.bottomRight().x()* PIXEL_SCALE
        # y_max =  -br.topLeft().y()* PIXEL_SCALE

        x_min = sp.x()* PIXEL_SCALE
        y_min =  -ep.y()* PIXEL_SCALE
        x_max = ep.x()* PIXEL_SCALE
        y_max =  -sp.y()* PIXEL_SCALE
        fov = 600 * PIXEL_SCALE
        if (x_max - x_min < fov and y_max - y_min < fov):
            print("Immediate move:")
            cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x_min:.3f} Y{y_min:.3f}"
            self.client.publish(f"{TARGET}/command", cmd)
        else:
            self.grid = []
            gx = x_min
            gy = y_max

            #self.grid.append("$H")
            # self.grid.append("$HY")
            #self.grid.append("$HY")

            while gy > y_min:
                while gx < x_max:
                    self.grid.append(f"$J=G90 G21 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f}")
                    gx += fov/2
                gx = x_min
                gy -= fov/2

            print(self.grid)
            cmd = self.grid.pop(0)
            print("Run kickoff command:", cmd)
            self.client.publish(f"{TARGET}/command", cmd)


    def eventFilter(self, widget, event):
        # return super().eventFilter(widget, event)

        # if widget != self.widget:
        #     return False
        if isinstance(event, QtGui.QMouseEvent):
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self.press = event.pos()
                return True
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                self.generateGrid(self.press, event.pos())
                return True
            
        elif isinstance(event, QtGui.QKeyEvent):
            #if not event.isAutoRepeat():
            if True:
                key = event.key()    
                type_ = event.type()

                if key == QtCore.Qt.Key_C and type_ == QtCore.QEvent.KeyPress:
                    print("cancel")
                    self.client.publish(f"{TARGET}/cancel", "")
                    return True
                elif key == QtCore.Qt.Key_S and type_ == QtCore.QEvent.KeyPress:
                    print("stop")
                    self.grid = []
                    return True
                    
                elif key == QtCore.Qt.Key_P and type_ == QtCore.QEvent.KeyPress:
                    fname = "image.%05d.png" % self.counter
                    if self.currentImage:
                        self.currentImage.convertToFormat(QtGui.QImage.Format_Grayscale8).save("movie/" + fname)
                        self.tile_config.write(f"{fname}; ; ({self.scale_pos[1]}, {-self.scale_pos[0]})\n")
                        self.tile_config.flush()
                        self.counter += 1
                    return True

                # elif type_ == QtCore.QEvent.KeyRelease and key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Plus, QtCore.Qt.Key_Minus):
                #     self.client.publish(f"{TARGET}/cancel", "")
                #     return True

                elif self.state == "Idle":
                    if key == QtCore.Qt.Key_Left and type_ == QtCore.QEvent.KeyPress:
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                        return True
                    elif key == QtCore.Qt.Key_Right and type_ == QtCore.QEvent.KeyPress:
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                        return True
                    elif key == QtCore.Qt.Key_Up and type_ == QtCore.QEvent.KeyPress:
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                        self.client.publish(f"{TARGET}/command", cmd)
                        return True
                    elif key == QtCore.Qt.Key_Down and type_ == QtCore.QEvent.KeyPress:
                        cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
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
    app = QApplication(sys.argv)
   
    app.exec_()
