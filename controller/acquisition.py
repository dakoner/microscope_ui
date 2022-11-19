import numpy as np
import sys
sys.path.append('..')
from microscope_ui.config import PIXEL_SCALE, TARGET, HEIGHT, WIDTH, FOV_X, FOV_Y, XY_FEED, Z_FEED
from PyQt5 import QtWidgets, QtGui, QtCore
from scanned_image import ScannedImage

class Acquisition():
    def __init__(self, lastRubberBand):
        self.lastRubberBand = lastRubberBand
        self.grid = []
        self.counter = 0
        self.scanned_image_tabwidget =  QtWidgets.QTabWidget()

    def startAcquisition(self):
        self.orig_grid = self.generateGrid(*self.lastRubberBand)
        
        self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
        width = int(self.lastRubberBand[1].x()-self.lastRubberBand[0].x())+WIDTH
        height = int(self.lastRubberBand[1].y()-self.lastRubberBand[0].y())+HEIGHT
        scanned_image = ScannedImage(width, height)
        self.scanned_image_tabwidget.addTab(scanned_image, str(self.counter))
        self.scanned_image_tabwidget.show()

        app=QtWidgets.QApplication.instance()
        self.grid = self.orig_grid[:]
        addr, cmd = self.grid.pop(0)
        app.client.publish(f"{TARGET}/command", cmd)


    def snapPhoto(self):
        app=QtWidgets.QApplication.instance()
        camera = app.camera
        draw_data = camera.image
        pos = camera.pos
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = app.main_window.tile_graphics_view.scene.addPixmap(pixmap)
        pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        pm.setZValue(1)
        app.main_window.image_view.setPixmap(pixmap)

        current_pos = QtCore.QPointF(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        self.scanned_image_tabwidget.widget(self.counter).addImage(current_pos-self.startPos, image)

    def doAcquisition(self):
        if len(self.grid):
            if self.grid == [None]:
                self.snapPhoto()
                self.scanned_image_tabwidget.widget(self.counter).save(f"c:\\Users\\dek\\Desktop\\acquisition\\frame.{self.counter}.tif")
                self.counter += 1
                self.startAcquisition()
            else:
                self.snapPhoto()
                addr, cmd = self.grid.pop(0)
                app=QtWidgets.QApplication.instance()
                app.client.publish(f"{TARGET}/command", cmd)

    def generateGrid(self, from_, to):
        grid = []
        dz = [0]

        x_min = from_.x()* PIXEL_SCALE
        y_min =  from_.y()* PIXEL_SCALE
        x_max = to.x()* PIXEL_SCALE
        y_max =  to.y()* PIXEL_SCALE

        app=QtWidgets.QApplication.instance()

        z = app.camera.pos[2]
        num_z = len(dz)
        ys = np.arange(y_min, y_max, FOV_Y)
        #ys = [y_min, y_max]
        num_y = len(ys)
        xs = np.arange(x_min, x_max, FOV_X)
        #xs = [x_min, x_max]
        num_x = len(xs)
        
        for i, deltaz in enumerate(dz):           
            for j, gy in enumerate(ys):
                # if j % 2 == 0:
                #     xs_ = xs
                # else:
                #     xs_ = xs[::-1]
                # print(xs_)
                ##Disable bidirectional scanning since it interferes with tile blending
                xs_ = xs
                for k, gx in enumerate(xs_):
                    curr_z = z + deltaz
                    g = f"$J=G90 G21 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f} Z{curr_z:.3f}"
                    grid.append(((i,j,k),g))

        grid.append(None)
        return grid