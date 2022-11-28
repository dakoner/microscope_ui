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

        self.x_min = from_.x()* PIXEL_SCALE
        self.y_min =  from_.y()* PIXEL_SCALE
        self.x_max = to.x()* PIXEL_SCALE
        self.y_max =  to.y()* PIXEL_SCALE

        app=QtWidgets.QApplication.instance()

        z = app.camera.pos[2]
        num_z = len(dz)
        self.ys = np.arange(self.y_min, self.y_max, FOV_Y)
        #ys = [y_min, y_max]
        num_y = len(self.ys)
        self.xs = np.arange(self.x_min, self.x_max, FOV_X)
        #xs = [x_min, x_max]
        num_x = len(self.xs)
        
        for i, deltaz in enumerate(dz):           
            for j, gy in enumerate(self.ys):
                # if j % 2 == 0:
                #     print("even")
                #     xs_ = xs
                # else:

                #     print("odd")
                #     xs_ = xs[::-1]
                # print(xs_)
                ##Disable bidirectional scanning since it interferes with tile blending
                xs_ = self.xs
                for k, gx in enumerate(xs_):
                    curr_z = z + deltaz
                    g = f"G90 G21 G1 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f} Z{curr_z:.3f}"
                    grid.append(((i,j,k),(gx,gy,curr_z),g))

        grid.append(None)
        return grid

    def startAcquisition(self):
        app=QtWidgets.QApplication.instance()
        self.grid = self.orig_grid[:]
        self.index, self.loc, cmd = self.grid.pop(0)
        app.main_window.label_counter.setText(str(self.counter))
        
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

        pm = app.main_window.tile_graphics_view.scene.addPixmap(pixmap)
        pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        pm.setZValue(1)

    def doAcquisition(self):
        app=QtWidgets.QApplication.instance()
        if len(self.grid):
            if self.grid == [None]:
                self.snapPhoto()
                self.counter += 1
                app.main_window.label_counter.setText(str(self.counter))
                self.startAcquisition()
            else:
                self.snapPhoto()
                self.index, self.loc, cmd = self.grid.pop(0)
                app.main_window.label_i.setText(f"{self.index[0]} of ?")
                app.main_window.label_j.setText(f"{self.index[1]} of {len(self.ys)}")
                app.main_window.label_k.setText(f"{self.index[2]} of {len(self.xs)}")
                app=QtWidgets.QApplication.instance()
                app.client.publish(f"{TARGET}/command", cmd)