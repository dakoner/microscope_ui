import ffmpeg
import tifffile
import json
import os
import time
import numpy as np
import sys
from PIL import Image
sys.path.append('..')
from config import PIXEL_SCALE, TARGET, HEIGHT, WIDTH, FOV_X, FOV_Y, FOV_X_PIXELS, FOV_Y_PIXELS, XY_FEED, Z_FEED
from PyQt5 import QtWidgets, QtGui, QtCore


class Acquisition():
    def __init__(self, lastRubberBand):
        self.app=QtWidgets.QApplication.instance()

        self.lastRubberBand = lastRubberBand
        self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
        self.grid = []
        self.counter = 0
        self.start_time = time.time()
        # self.prefix = os.path.join("movie", str(self.start_time))
        # os.makedirs(self.prefix)
        self.prefix = os.path.join("photo", str(self.start_time))
        os.makedirs(self.prefix)
        self.orig_grid = self.generateGrid(*self.lastRubberBand)
        self.inner_counter = 0
        self.block = None
        self.out = None
        self.fname = None
        self.vs = []

        
    def imageChanged(self, frame):
        print('snapshot', time.time())
        self.process.stdin.write(frame.astype(np.uint8).tobytes())
       

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
        num_y = len(self.ys)
        self.xs = np.arange(self.x_min, self.x_max, FOV_X)
        num_x = len(self.xs)

        grid.append([
            ["MOVE_TO", (self.xs[0],self.ys[0],z), (0,0,0), 100]])
        grid.append([
             ["WAIT"]])
        #grid.append([
        #    ["START_MOVIE"] ])
       
        for i, deltaz in enumerate(self.zs):           
            curr_z = z + deltaz
            for j, gy in enumerate(self.ys):
                #for k, gx in enumerate(self.xs):
                if j % 2:
                    grid.append([
                        ["MOVE_TO", (self.xs[0],gy,curr_z), (0,j,0), 10],
                        ["MOVE_TO", (self.xs[-1],gy,curr_z), (len(self.xs),j,0), 10]])
                else:
                    grid.append([
                        ["MOVE_TO", (self.xs[-1],gy,curr_z), (len(self.xs),j,0), 10],
                        ["MOVE_TO", (self.xs[0],gy,curr_z), (0,j,0), 10]])

        grid.append([["WAIT"]])
        grid.append([["DONE"]])

        with open(os.path.join(self.prefix, "scan_config.json"), "w") as scan_config:
            json.dump({
                    "i_dim": len(self.zs),
                    "j_dim": len(self.ys),
                    "k_dim": len(self.xs),
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
        print("grid:", grid)
        return grid

    def startAcquisition(self):
        self.grid = self.orig_grid[:]
        self.app.main_window.serial.stateChanged.connect(self.acq)
        self.app.main_window.serial.messageChanged.connect(self.output)
        self.m_pos_ts = []
        self.app.main_window.serial.posChanged.connect(self.pos)
        self.time_0 = time.time()
        self.counter = 0
        
        self.process = (
        ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(1280, 1024), r=100)
            .output("movie.mp4", pix_fmt='yuv420p', vcodec='libx264', r=100)#, preset="ultrafast", crf=50)
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )
        self.app.main_window.camera.imageChanged.connect(self.imageChanged)
        self.doCmd()
        # print("cmd=", cmd)
        # self.app.main_window.label_counter.setText(str(self.counter))
        

    def pos(self, x, y, z, t):
        #print("x, y, z, t", x, y, z, t)
        self.m_pos = x, y, z
        self.m_pos_t = t
        self.m_pos_ts.append( (self.m_pos, t))

    def doCmd(self):
        print('block:', self.block)
        if self.block is None or self.block == []:
            self.block = self.grid.pop(0)
        print("self.block: ", self.block)
       

        subcmd = self.block.pop(0)
    
        self.cur = subcmd
        print("Subcmd", subcmd[0])
        if subcmd[0] == 'HOME_X':
            g = f"$HX\n"
            self.app.main_window.serial.write(g)
        elif subcmd[0] == 'HOME_Y':
            g = f"$HY\n"
            self.app.main_window.serial.write(g)    
        elif subcmd[0] == "MOVE_TO":
            print("MOVE_TO")
            self.x, self.y, self.z = subcmd[1]
            self.k, self.j, self.i = subcmd[2]
            f = subcmd[3]
            pos = self.app.main_window.m_pos
            if pos[0] == self.x and pos[1] == self.y and pos[2] == self.z:
                print("already at position")
            else:
                g = f"G90 G21 G1 F{f} X{self.x:.3f} Y{self.y:.3f} Z{self.z:.3f}\n"
                self.app.main_window.serial.write(g)
                self.app.main_window.label_k.setText(f"col {self.k+1} of {len(self.xs)}")
                self.app.main_window.label_j.setText(f"row {self.j+1} of {len(self.ys)}")
                self.app.main_window.label_i.setText(f"dep {self.i+1} of {len(self.zs)}")
        elif subcmd[0] == 'WAIT':
            print("Waiting")
            self.app.main_window.serial.write("G4 P1\n")
        elif subcmd[0] == 'DONE':
            self.app.main_window.tile_graphics_view.stopAcquisition()
            self.app.main_window.camera.imageChanged.disconnect(self.imageChanged)
            print('done')
           
            self.process.stdin.close()
            self.process.wait()
            del self.process
        else:
            print("Unknown subcmd", subcmd)
                
    def output(self, output):
        #print("output", output)
        if output == 'ok' and self.cur[0] == 'WAIT':
            #print('go to next')
            self.doCmd()

    def acq(self, state):
        #print("acq", state)
        if state == 'Idle' and self.cur[0] == 'MOVE_TO':
            #print("go to next")
            self.doCmd()

    # def startTrigger(self, i, j, k):
    #     #self.app.main_window.camera.stopWorker()
    #     self.app.main_window.setTrigger()
    #     self.image_thread = ImageThread(self, i, j, k)
    #     self.image_thread.start()
    #     time.sleep(1)

    # def endTrigger(self):
    #     self.image_thread.finished = True
    #     time.sleep(1)
    #     #self.app.main_window.camera.startWorker()
    #     self.app.main_window.setContinuous()
