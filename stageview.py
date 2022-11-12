import numpy as np
import tifffile
import os
import time
import json
import sys
sys.path.append("..")
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
from image_zmq_camera_reader import ImageZMQCameraReader
from scene import Scene
from mqtt_qobject import MqttClient
from config import PIXEL_SCALE, TARGET, XY_FEED, Z_FEED, WIDTH, HEIGHT, FOV_X, FOV_X_PIXELS, FOV_Y, FOV_Y_PIXELS


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
        #self.main_window._tile_window.ensureVisible(self.scene.borderRect)


        self.dro_window = DRO(parent=self.main_window._image_window)
        self.dro_window.show()
        self.dro_window.setAutoFillBackground(True)
        self.dro_window.raise_()

        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)
        self.currentImage = None

        self.acquisition = False
        self.tile_window = QtWidgets.QTabWidget()

    def cancel(self):
        self.client.publish(f"{TARGET}/cancel", "")

    def moveTo(self, position):
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}"
        self.client.publish(f"{TARGET}/command", cmd)
 
    def generateGrid(self, start_event, end_event):
        sp = start_event
        ep = end_event
        x = sp.x()
        y = sp.y()
        width = ep.x()-x
        height = ep.y()-y


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
        

        self.grid = []
        dz = [-0.2, -0.1, 0, 0.1, 0.2]
        

        #self.grid.append("$H")
        # self.grid.append("$HY")
        #self.grid.append("$HY")

        z = self.currentPosition[2]
        num_z = len(dz)
        ys = np.arange(y_min, y_max, FOV_Y)
        num_y = len(ys)
        xs = np.arange(x_min, x_max, FOV_X)
        num_x = len(xs)
        

        self.dimensions = (num_z, num_y, num_x)

        for i, deltaz in enumerate(dz):
            for j, gy in enumerate(ys):
                for k, gx in enumerate(xs):
                    curr_z = z + deltaz
                    g = f"$J=G90 G21 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f} Z{curr_z:.3f}"
                    self.grid.append(((i,j,k),g))

        #print(self.grid)

        if len(self.grid):
            self.prefix= "movie/" + str(int(time.time()))
            os.makedirs(self.prefix)
            with open(f"{self.prefix}/acquisition_config.json", "w") as w:
                r = {
                'pixel_scale': PIXEL_SCALE,
                'fov_x': FOV_X,
                'fov_y': FOV_Y,   
                'width': WIDTH,
                'height': HEIGHT
                }
                json.dump(r, w)
            self.acq_counter = 0
            self.tile_config = open(f"{self.prefix}/tile_config.json", "w")
            self.startAcquisition()


    def startAcquisition(self):
        self.acquisition = True

        self.counter = 0

        # set up to hold space for n_z, n_c, n_y, n_x
        print("kickoff")
        self.orig_grid = self.grid[:]
        addr, cmd = self.grid.pop(0)
        self.array_index = addr
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
        # Z not scaled because it's already in mm
        self.scale_pos = pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE, pos[2]
        self.dro_window.x_value.display(pos[0])
        self.dro_window.y_value.display(pos[1])
        self.dro_window.z_value.display(pos[2])
        self.dro_window.state_value.setText(self.state)



        self.draw_data = draw_data
        self.currentImage = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        currentPixmap = QtGui.QPixmap.fromImage(self.currentImage.mirrored(horizontal=False, vertical=False))
        self.main_window._image_window.setPixmap(currentPixmap)
        self.main_window._image_window.adjustSize()

        if self.state != 'Home': 
            if not self.scene.currentRect:
                pen = QtGui.QPen()
                pen.setWidth(20)
                color = QtGui.QColor(QtCore.Qt.red)
                #color.setAlpha(1)
                brush = QtGui.QBrush(color)
                self.scene.currentRect = self.scene.addRect(0, 0, draw_data.shape[1], draw_data.shape[0], pen=pen, brush=brush)
                self.scene.currentRect.setZValue(20)

            self.scene.currentRect.setPos(self.scale_pos[0], self.scale_pos[1])

            if not self.acquisition:
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
                if a > 300000:# and [item for item in ci if isinstance(item, QtWidgets.QGraphicsPixmapItem)] == []:
                    pm = self.scene.addPixmap(currentPixmapFlipped)
                    pm.setPos(self.scale_pos[0], self.scale_pos[1])
                    pm.setZValue(2)
        
        self.scene.update()


        if went_idle:
            if self.acquisition:
                if len(self.grid) == 0:
                    self.snapPhoto()
                    self.acquisition = False
                    
                    self.grid = self.orig_grid[:]
                    self.acq_counter += 1
                    if self.acq_counter < 7:
                        self.startAcquisition()
                    else:
                        self.tile_config.close()
                else:
                    print("collect acquisition frame (%d remaining)" % len(self.grid))
                    self.snapPhoto()
                    currentPixmapFlipped = QtGui.QPixmap.fromImage(self.currentImage.mirrored(horizontal=False, vertical=False))
                    pm = self.scene.addPixmap(currentPixmapFlipped)
                    pm.setPos(self.scale_pos[0], self.scale_pos[1])
                    pm.setZValue(2)

                    addr, cmd = self.grid.pop(0)
                    self.array_index = addr
                    self.client.publish(f"{TARGET}/command", cmd)
        
    def snapPhoto(self):
        fname = f"{self.prefix}/{self.acq_counter}_{self.counter}.tiff"
        self.currentImage.save(fname)
        r = {
            'fname': fname,
            'gz': self.array_index[0],
            'gy': self.array_index[1],
            'gx': self.array_index[2],
            'acquisition_counter': self.acq_counter,
            'x': self.scale_pos[1],
            'y': self.scale_pos[0],
            'z': self.scale_pos[2],
        }
        json.dump(r, self.tile_config)
        self.tile_config.write("\n")
        self.tile_config.flush()
        self.counter += 1

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
   
    app.exec_()