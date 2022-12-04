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
        self.app=QtWidgets.QApplication.instance()

        self.lastRubberBand = lastRubberBand
        self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
        self.grid = []
        self.counter = 0

        self.start_time = time.time()

        self.prefix = os.path.join("movie", str(self.start_time))
        os.makedirs(self.prefix)
        self.orig_grid = self.generateGrid(*self.lastRubberBand)
        
        self.tile_config = open(os.path.join(self.prefix, "tile_config.json"), "w")
        self.inner_counter = 0
        self.block = None
        
    # def __del__(self):
    #     print("deleteme")
        #self.tile_config.close()
        
    def generateGrid(self, from_, to):
        grid = []
        #self.zs = [-0.2,-0.1,0,0.1,0.2]
        self.zs = [0]
        
        self.x_min = from_.x()* PIXEL_SCALE
        self.y_min =  from_.y()* PIXEL_SCALE
        self.x_max = to.x()* PIXEL_SCALE
        self.y_max =  to.y()* PIXEL_SCALE
        self.z_min = self.zs[0]
        self.z_max = self.zs[-1]

        z = self.app.m_pos[2]
        num_z = len(self.zs)
        self.ys = np.arange(self.y_min, self.y_max, FOV_Y)
        #ys = [y_min, y_max]
        num_y = len(self.ys)
        self.xs = np.arange(self.x_min, self.x_max, FOV_X)
        #self.xs = [self.x_min, self.x_max]
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
                inner_grid = []
                for k, gx in enumerate(xs_):
                    curr_z = z + deltaz
                    inner_grid.append(["MOVE_TO", (gx,gy,curr_z), (i,j,k)])
                    inner_grid.append(["WAIT"])
                    inner_grid.append(["PHOTO", (gx,gy,curr_z), (i,j,k)])

                    #g = f"G90 G21 G1 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f} Z{curr_z:.3f}"
                grid.append(inner_grid)

        grid.append(["DONE"])

        with open(os.path.join(self.prefix, "scan_config.json"), "w") as scan_config:
            json.dump({
                    "i_dim": i+1,
                    "j_dim": j+1,
                    "k_dim": k+1,
                    "x_min": self.x_min,
                    "y_min": self.y_min,
                    "z_min": self.z_min,
                    "x_max": self.x_max,
                    "y_max": self.y_max,
                    "z_max": self.z_max,
                    "pixel_scale": PIXEL_SCALE,
                    "fov_x_pixels": FOV_X_PIXELS,
                    "fov_y_pixels": FOV_Y_PIXELS,
                }, scan_config)
        return grid

    def startAcquisition(self):
        self.grid = self.orig_grid[:]
        self.app.stateChanged.connect(self.acq)
        self.app.outputChanged.connect(self.output)

        self.doCmd()
        # print("cmd=", cmd)
        # self.app.main_window.label_counter.setText(str(self.counter))
        

    def doCmd(self):
        if self.block is None or self.block == []:
            self.block = self.grid.pop(0)
       

        subcmd = self.block.pop(0)
    
        self.cur = subcmd
        if subcmd[0] == "MOVE_TO":
            x, y, z = subcmd[1]
            i, j, k = subcmd[2]
            g = f"G90 G21 G1 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f} Z{z:.3f}"
            self.app.client.publish(f"{TARGET}/command", g)
            self.app.main_window.label_i.setText(f"{i} of {len(self.zs)}")
            self.app.main_window.label_j.setText(f"{j} of {len(self.ys)}")
            self.app.main_window.label_k.setText(f"{k} of {len(self.xs)}")
        elif subcmd[0] == 'WAIT':
            self.app.client.publish(f"{TARGET}/command", "G4 P0.1")
        elif subcmd[0] == 'PHOTO':
            x, y, z = subcmd[1]
            i, j, k = subcmd[2]
            self.snapPhoto(x, y, z, i, j, k)
            self.doCmd()
        else:
            print("Unknown subcmd", subcmd)
                
    def output(self, output):
        if output == 'ok' and self.cur[0] == 'WAIT':
            self.doCmd()

    def acq(self, state):
        if state == 'Idle' and self.cur[0] == 'MOVE_TO':
            self.doCmd()

    # def doAcquisition(self):
    #     if len(self.grid):
   
    #             self.app.main_window.label_counter.setText(str(self.counter))
    #             self.startAcquisition()
    #         else:
    #             
    #             t = time.time() - self.start_time
    #             self.app.main_window.label_time.setText(f"{t:.1f} seconds since starting.")
    #             total = (self.mi[0]+1) * (self.mi[1]+1) * (self.mi[2]+1)
    #             self.app.main_window.label_completion.setText(f"{self.inner_counter} of {total}")
    #             self.inner_counter += 1
    #             self.app.client.publish(f"{TARGET}/command", cmd)


    def snapPhoto(self, x, y, z, i, j, k):
        camera = self.app.camera
        draw_data = camera.image
        pos = self.app.m_pos
        
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_Grayscale8)
        # #a = QtGui.QImage(image.width(), image.height(), QtGui.QImage.Format_ARGB32)
        # #a.fill(QtGui.QColor(255, 255, 255, 255))
        # #image.setAlphaChannel(a)
        fname = os.path.join(self.prefix, f"image_{self.counter}_{i}_{j}_{k}.tif")
        image.save(fname)

        pixmap = QtGui.QPixmap.fromImage(image)
        pm = self.app.main_window.tile_graphics_view.scene.addPixmap(pixmap)
        pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        pm.setZValue(1)

        json.dump({
            "fname": os.path.basename(fname),
            "counter": self.counter,
            "i": i,
            "j": j,
            "k": k,
            "x": x,
            "y": y,
            "z": z,
        }, self.tile_config)
        self.tile_config.write("\n")
        self.tile_config.flush()