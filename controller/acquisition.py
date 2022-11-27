import json
import os
import time
import numpy as np
import sys
sys.path.append('..')
from microscope_ui.config import PIXEL_SCALE, TARGET, HEIGHT, WIDTH, FOV_X, FOV_Y, XY_FEED, Z_FEED
from PyQt5 import QtWidgets, QtGui, QtCore

class Acquisition():
    def __init__(self, lastRubberBand):
        self.lastRubberBand = lastRubberBand
        self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
        self.grid = []
        self.counter = 0

        self.prefix = os.path.join("movie", str(int(time.time())))
        os.makedirs(self.prefix)
        self.orig_grid = self.generateGrid(*self.lastRubberBand)
        indices = [value[0] for value in self.orig_grid if value]
        locs = [value[1] for value in self.orig_grid if value]
        mi=max(indices)
        min_locs=max(locs)
        max_locs=max(locs)
        with open(os.path.join(self.prefix, "scan_config.json"), "w") as scan_config:
            json.dump({
                    "i_dim": mi[0]+1,
                    "j_dim": mi[1]+1,
                    "k_dim": mi[2]+1,
                    "x_min": min_locs[0],
                    "y_min": min_locs[1],
                    "z_min": min_locs[2],
                    "x_max": max_locs[0],
                    "y_max": max_locs[1],
                    "z_max": max_locs[2]
                }, scan_config)
        self.tile_config = open(os.path.join(self.prefix, "tile_config.json"), "w")

    def __del__(self):
        self.tile_config.close()
        
    def generateGrid(self, from_, to):
        grid = []
        #dz = np.linspace(-2, 2, 25)
        dz = [0]
        #print(dz)
        #dz = [-.25, -0.2, -0.15, -0.1, -0.05, 0, 0.05, 0.1, 0.15, 0.2, 0.25]

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
                    grid.append(((i,j,k),(gx,gy,curr_z),g))

        grid.append(None)
        return grid

    def startAcquisition(self):
        app=QtWidgets.QApplication.instance()
        self.grid = self.orig_grid[:]
        self.index, self.loc, cmd = self.grid.pop(0)
        
        app.client.publish(f"{TARGET}/command", cmd)

    def snapPhoto(self):
        app=QtWidgets.QApplication.instance()
        camera = app.camera
        draw_data = camera.image
        pos = camera.pos
        
        fname = os.path.join(self.prefix, f"image_{self.counter}_{self.index[0]}_{self.index[1]}_{self.index[2]}.tif")
        json.dump({
            "fname": os.path.basename(fname),
            "counter": self.counter,
            "i": self.index[0],
            "j": self.index[1],
            "k": self.index[2],
        }, self.tile_config)
        self.tile_config.write("\n")
        self.tile_config.flush()

        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        #a = QtGui.QImage(image.width(), image.height(), QtGui.QImage.Format_ARGB32)
        #a.fill(QtGui.QColor(255, 255, 255, 255))
        #image.setAlphaChannel(a)
        image.save(fname)

        pixmap = QtGui.QPixmap.fromImage(image)
        app.main_window.image_view.setPixmap(pixmap)
        print("add image, for acquisition")

        pm = app.main_window.tile_graphics_view.scene.addPixmap(pixmap)
        pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        pm.setZValue(1)

    def doAcquisition(self):
        if len(self.grid):
            if self.grid == [None]:
                self.snapPhoto()
                app=QtWidgets.QApplication.instance()
                camera = app.camera
                pos = camera.pos
                self.counter += 1
                self.startAcquisition()
            else:
                self.snapPhoto()
                self.index, self.loc, cmd = self.grid.pop(0)
                app=QtWidgets.QApplication.instance()
                app.client.publish(f"{TARGET}/command", cmd)