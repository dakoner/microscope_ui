import tifffile
import cv2
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
        
        #ppself.app.camera.imageChanged.connect(self.imageChanged)
        self.out = None
        self.fname = None
        self.vs = []

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

        z = self.app.main_window.m_pos[2]
        num_z = len(self.zs)
        self.ys = np.arange(self.y_min, self.y_max, FOV_Y)
        #ys = [y_min, y_max]
        num_y = len(self.ys)
        self.xs = np.arange(self.x_min, self.x_max, FOV_X)
        self.xs = [self.x_min, self.x_max]
        num_x = len(self.xs)


        for i, deltaz in enumerate(self.zs):           
            curr_z = z + deltaz
            for j, gy in enumerate(self.ys):
                inner_grid = []
                inner_grid.append(["MOVE_TO", (self.xs[0],gy,curr_z), (i,j,0)])
                inner_grid.append(["WAIT"])
                inner_grid.append(["START_TRIGGER"])
                inner_grid.append(["MOVE_TO", (self.xs[1],gy,curr_z), (i,j,1)])
                inner_grid.append(["WAIT"])
                inner_grid.append(["END_TRIGGER"])
                grid.append(inner_grid)

        grid.append(["DONE"])

        # with open(os.path.join(self.prefix, "scan_config.json"), "w") as scan_config:
        #     json.dump({
        #             "i_dim": i+1,
        #             "j_dim": j+1,
        #             "k_dim": k+1,
        #             "x_min": self.x_min,
        #             "y_min": self.y_min,
        #             "z_min": self.z_min,
        #             "x_max": self.x_max,
        #             "y_max": self.y_max,
        #             "z_max": self.z_max,
        #             "pixel_scale": PIXEL_SCALE,
        #             "fov_x_pixels": FOV_X_PIXELS,
        #             "fov_y_pixels": FOV_Y_PIXELS,
        #         }, scan_config)
        return grid

    def startAcquisition(self):
        self.grid = self.orig_grid[:]
        self.app.main_window.serial.stateChanged.connect(self.acq)
        self.app.main_window.serial.messageChanged.connect(self.output)

        self.doCmd()
        # print("cmd=", cmd)
        # self.app.main_window.label_counter.setText(str(self.counter))
        

    def doCmd(self):
        print("self.block: ", self.block)
        if self.block is None or self.block == []:
            self.block = self.grid.pop(0)
       

        subcmd = self.block.pop(0)
    
        self.cur = subcmd
        print(self.cur)
        
        if subcmd[0] == "MOVE_TO":
            x, y, z = subcmd[1]
            i, j, k = subcmd[2]
            pos = self.app.main_window.m_pos
            if pos[0] == x and pos[1] == y and pos[2] == z:
                print("already at position")
            else:
                g = f"G90 G21 G1 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f} Z{z:.3f}\n"
                self.app.main_window.serial.write(g)
                self.app.main_window.label_i.setText(f"{i} of {len(self.zs)}")
                self.app.main_window.label_j.setText(f"{j} of {len(self.ys)}")
                self.app.main_window.label_k.setText(f"{k} of {len(self.xs)}")
        elif subcmd[0] == 'WAIT':
            self.app.main_window.serial.write("G4 P0.1\n")
        elif subcmd[0] == 'START_TRIGGER':
            self.startTrigger()
            print("started trigger, doing next command")
            self.doCmd()
        elif subcmd[0] == 'END_TRIGGER':
            self.endTrigger()
            self.doCmd()
        else:
            print("Unknown subcmd", subcmd)
                
    def output(self, output):
        print("output", output)
        if output == 'ok' and self.cur[0] == 'WAIT':
            print('go to next')
            self.doCmd()

    def acq(self, state):
        print("acq", state)
        if state == 'Idle' and self.cur[0] == 'MOVE_TO':
            print("go to next")
            self.doCmd()

    def startTrigger(self):
        class ImageThread(QtCore.QThread):
            def __init__(self, parent):
                super().__init__()
                self.counter = 0
                self.finished = False
                self.parent = parent
                self.app = parent.app

            def run(self):
                while not self.finished:
                    self.app.main_window.microscope_esp32_controller_serial.write("\nX251 0\n")
                    image_result = self.app.main_window.camera.camera.GetNextImage()
                    if image_result.IsIncomplete():
                        print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                    else:
                        d = image_result.GetNDArray()
                        print("Got image", d.shape)
                        tifffile.imwrite("test.%d.png" % self.counter, d)
                        #self.parent.doCmd()
                        self.counter += 1
                    time.sleep(0.1)

        self.app.main_window.camera.stopWorker()
        self.app.main_window.setTrigger()
        self.image_thread = ImageThread(self)
        self.image_thread.start()
        time.sleep(1)
        print("start trigger done")
        #self.microscope_esp32_controller_serial.write("\nX251 0\n")
        #time.sleep(1)
        #image_result = self.camera.camera.GetNextImage()
        #if image_result.IsIncomplete():
        #    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
        #else:
        #    d = image_result.GetNDArray()
        #    print(d)
        #time.sleep(1)
        # print("setcont")

    def endTrigger(self):
        self.image_thread.finished = True
        time.sleep(1)
        self.app.main_window.camera.startWorker()
        self.app.main_window.setContinuous()

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


    # def imageChanged(self, draw_data):
    #     if self.fname:
    #         # val = draw_data.sum()/ (draw_data.shape[0]*draw_data.shape[1])
    #         # if val > 10:
    #         #     d = np.repeat(draw_data, 3, axis=2)
    #         #     self.data.append(d)

    # def startVideo(self, x, y, i, j):
    #     self.fname = os.path.join(self.prefix, f"output.{i},{j}.mkv")
    #     self.data = []

    # def stopVideo(self):
    #     class VideoSaver(QtCore.QThread):
    #         def __init__(self, out, data):
    #             super().__init__()
    #             self.out = out
    #             self.data = data
    #         def run(self):
    #             for frame in self.data:
    #                 self.out.write(frame)
    #             self.out.release()
    #             print("done")

    #     fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #     self.out = cv2.VideoWriter(self.fname, fourcc, 60.0, (WIDTH, HEIGHT))
    #     v = VideoSaver(self.out, self.data.copy())
    #     self.vs.append(v)
    #     v.start()
    #     self.data = None
    #     self.fname = None

    # def snapPhoto(self, x, y, z, i, j, k):
    #     camera = self.app.camera
    #     draw_data = camera.image
    #     pos = self.app.main_window.m_pos
        
    #     image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_Grayscale8)
    #     # #a = QtGui.QImage(image.width(), image.height(), QtGui.QImage.Format_ARGB32)
    #     # #a.fill(QtGui.QColor(255, 255, 255, 255))
    #     # #image.setAlphaChannel(a)
    #     fname = os.path.join(self.prefix, f"image_{self.counter}_{i}_{j}_{k}.tif")
    #     image.save(fname)

    #     pixmap = QtGui.QPixmap.fromImage(image)
    #     pm = self.app.main_window.tile_graphics_view.scene.addPixmap(pixmap)
    #     pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
    #     pm.setZValue(1)

    #     json.dump({
    #         "fname": os.path.basename(fname),
    #         "counter": self.counter,
    #         "i": i,
    #         "j": j,
    #         "k": k,
    #         "x": x,
    #         "y": y,
    #         "z": z,
    #     }, self.tile_config)
    #     self.tile_config.write("\n")
    #     self.tile_config.flush()