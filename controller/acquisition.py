import json
import os
import time
import numpy as np
import sys
sys.path.append('..')
from microscope_ui.config import PIXEL_SCALE, TARGET, HEIGHT, WIDTH, FOV_X, FOV_Y, FOV_X_PIXELS, FOV_Y_PIXELS, XY_FEED, Z_FEED
from PyQt5 import QtWidgets, QtGui, QtCore

class Acquisition():
    def __init__(self, lastRubberBand):
        self.lastRubberBand = lastRubberBand
        self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
        self.grid = []
        self.counter = 0

        self.start_time = time.time()

        self.prefix = os.path.join("movie", str(self.start_time))
        os.makedirs(self.prefix)
        self.orig_grid = self.generateGrid(*self.lastRubberBand)
        indices = [value[0] for value in self.orig_grid if value]
        locs = [value[1] for value in self.orig_grid if value]
        self.mi=max(indices)
        min_locs=max(locs)
        max_locs=max(locs)
        with open(os.path.join(self.prefix, "scan_config.json"), "w") as scan_config:
            json.dump({
                    "i_dim": self.mi[0]+1,
                    "j_dim": self.mi[1]+1,
                    "k_dim": self.mi[2]+1,
                    "x_min": min_locs[0],
                    "y_min": min_locs[1],
                    "z_min": min_locs[2],
                    "x_max": max_locs[0],
                    "y_max": max_locs[1],
                    "z_max": max_locs[2],
                    "pixel_scale": PIXEL_SCALE,
                    "fov_x_pixels": FOV_X_PIXELS,
                    "fov_y_pixels": FOV_Y_PIXELS,
                }, scan_config)
        self.tile_config = open(os.path.join(self.prefix, "tile_config.json"), "w")
        self.inner_counter = 0

    def __del__(self):
        self.tile_config.close()
        
    def generateGrid(self, from_, to):
        grid = []
        self.zs = [-0.2,-0.1,0,0.1,0.2]
        
        self.x_min = from_.x()* PIXEL_SCALE
        self.y_min =  from_.y()* PIXEL_SCALE
        self.x_max = to.x()* PIXEL_SCALE
        self.y_max =  to.y()* PIXEL_SCALE

        app=QtWidgets.QApplication.instance()

        z = app.camera.pos[2]
        num_z = len(self.zs)
        self.ys = np.arange(self.y_min, self.y_max, FOV_Y)
        #ys = [y_min, y_max]
        num_y = len(self.ys)
        self.xs = np.arange(self.x_min, self.x_max, FOV_X)
        #xs = [x_min, x_max]
        num_x = len(self.xs)
        
        for i, deltaz in enumerate(self.zs):           
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
            "x": self.loc[0],
            "y": self.loc[1],
            "z": self.loc[2],
        }, self.tile_config)
        self.tile_config.write("\n")
        self.tile_config.flush()

        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_Grayscale8)
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
                self.inner_counter = 0
                self.counter += 1
                app.main_window.label_counter.setText(str(self.counter))
                self.startAcquisition()
            else:
                self.snapPhoto()
                self.index, self.loc, cmd = self.grid.pop(0)
                app.main_window.label_i.setText(f"{self.index[0]+1} of {len(self.zs)}")
                app.main_window.label_j.setText(f"{self.index[1]+1} of {len(self.ys)}")
                app.main_window.label_k.setText(f"{self.index[2]+1} of {len(self.xs)}")
                t = time.time() - self.start_time
                app.main_window.label_time.setText(f"{t:.1f} seconds since starting.")
                total = (self.mi[0]+1) * (self.mi[1]+1) * (self.mi[2]+1)
                app.main_window.label_completion.setText(f"{self.inner_counter} of {total}")
                self.inner_counter += 1
                app=QtWidgets.QApplication.instance()
                app.client.publish(f"{TARGET}/command", cmd)