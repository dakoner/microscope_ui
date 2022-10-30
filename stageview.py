import json
import sys
sys.path.append("..")
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
from image_zmq_camera_reader import ImageZMQCameraReader
from scene import Scene
from mqtt_qobject import MqttClient

from config import PIXEL_SCALE, TARGET, XY_FEED, Z_FEED, BIGSTITCH

def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("stageview.ui", self)

class DRO(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("dro.ui", self)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi.local"
        self.client.connectToHost()

        self.scene = Scene(self)

        self.state = "None"
        self.grid = []
        self.currentPosition = None

        self.main_window = MainWindow()
        self.main_window.show()

        self.main_window._tile_window.setScene(self.scene)
        self.main_window._tile_window.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)


        self.dro_window = DRO(parent=self.main_window._image_window)
        self.dro_window.show()
        self.dro_window.setAutoFillBackground(True)
        self.dro_window.raise_()

        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)
        self.currentImage = None


        self.tile_config = open("movie/TileConfiguration.txt", "w")
        self.tile_config.write("dim=2\n")
        self.tile_config.flush()
        self.counter = 0

        self.acquisition = False

    def moveTo(self, position):
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        print("moveTo", position, x, y)
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}"
        self.client.publish(f"{TARGET}/command", cmd)
 
    def generateGrid(self, start_event, end_event):
        sp = start_event
        ep = end_event
        x = sp.x()
        y = sp.y()
        width = ep.x()-x
        height = ep.y()-y
        print(x, y, width, height)


        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(50)
        color = QtGui.QColor(QtCore.Qt.black)
        color.setAlpha(0)
        brush = QtGui.QBrush(color)
        rect = self.scene.addRect(x, y, width, height, pen=pen, brush=brush)
        rect.setZValue(1)


        x_min = sp.x()* PIXEL_SCALE
        y_min =  sp.y()* PIXEL_SCALE
        x_max = ep.x()* PIXEL_SCALE
        y_max =  ep.y()* PIXEL_SCALE
        fov_x = 600 * PIXEL_SCALE
        fov_y = 400 * PIXEL_SCALE

        self.grid = []
        gx = x_min 
        gy = y_min

        #self.grid.append("$H")
        # self.grid.append("$HY")
        #self.grid.append("$HY")
        print(x_min, x_max)
        print(y_min, y_max)
        while gy < y_max - fov_y:
            while gx < x_max - fov_x:
                self.grid.append(f"$J=G90 G21 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f}")
                gx += fov_x
            gx = x_min
            gy += fov_y

        print(self.grid)
        self.acquisition = True
        if len(self.grid):
            print("kickoff")
            cmd = self.grid.pop(0)
            self.client.publish(f"{TARGET}/command", cmd)

    def imageTo(self, message, draw_data):
        m = json.loads(message)
        state = m['state']
        went_idle=False
        if self.state != 'Idle' and state == 'Idle':
            went_idle=True
        self.state = state
        self.currentPosition = m['m_pos']

        pos = self.currentPosition
        self.scale_pos = pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE, pos[2]/PIXEL_SCALE
        self.dro_window.x_value.display(pos[0])
        self.dro_window.y_value.display(pos[1])
        self.dro_window.z_value.display(pos[2])
        self.dro_window.state_value.setText(self.state)




        self.currentImage = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        currentPixmap = QtGui.QPixmap.fromImage(self.currentImage.mirrored(horizontal=False, vertical=False))
        self.main_window._image_window.setPixmap(currentPixmap)
        self.main_window._image_window.adjustSize()

        if self.state != 'Home':
            self.scene.currentRect.setPos(self.scale_pos[0], self.scale_pos[1])

            currentPixmapFlipped = QtGui.QPixmap.fromImage(self.currentImage.mirrored(horizontal=False, vertical=False))
            self.scene.pixmap.setPixmap(currentPixmap)
            self.scene.pixmap.setPos(self.scale_pos[0], self.scale_pos[1])

            #self.main_window._image_window.setScaledContents(True)

            ci = self.scene.pixmap.collidingItems()
            # Get the qpainterpath corresponding to the current image location, minus any overlapping images
            qp = QtGui.QPainterPath()
            qp.addRect(self.scene.pixmap.sceneBoundingRect())
            qp2 = QtGui.QPainterPath()
            for item in ci:
                if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                    qp2.addRect(item.sceneBoundingRect())

            qp3 = qp.subtracted(qp2)
            p = qp3.toFillPolygon()
            a = calculate_area(p)

            if a > 240000:# and [item for item in ci if isinstance(item, QtWidgets.QGraphicsPixmapItem)] == []:
                pm = self.scene.addPixmap(currentPixmapFlipped)
                pm.setPos(self.scale_pos[0], self.scale_pos[1])
                pm.setZValue(2)
            
        self.scene.update()

        if went_idle:
            if self.acquisition:
                if len(self.grid) == 0:
                    print("stop acquisition")
                    self.acquisition = False
                else:
                    print("collect acquisition frame (%d remaining)" % len(self.grid))
                    fname = "image.%d.png" % self.counter
                    if self.currentImage is not None:
                        self.currentImage.convertToFormat(QtGui.QImage.Format_Grayscale8).save("movie/" + fname)
                        if BIGSTITCH:
                            index = str(self.counter)
                        else:
                            index = fname
                        self.tile_config.write(f"{index}; ; ({self.scale_pos[0]}, {self.scale_pos[1]})\n")
                        self.tile_config.flush()
                        self.counter += 1

                    cmd = self.grid.pop(0)
                    self.client.publish(f"{TARGET}/command", cmd)
        

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
   
    app.exec_()