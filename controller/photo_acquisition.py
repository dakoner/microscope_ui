import tifffile

# import cv2
import json
import os
import time
import numpy as np
import sys
from PIL import Image

sys.path.append("..")
from config import (
    PIXEL_SCALE,
    TARGET,
    HEIGHT,
    WIDTH,
    FOV_X,
    FOV_Y,
    FOV_X_PIXELS,
    FOV_Y_PIXELS,
    XY_FEED,
    Z_FEED,
)
from PyQt6 import QtWidgets, QtGui, QtCore


class ImageThread(QtCore.QThread):
    def __init__(self, parent, i, j, k):
        super().__init__()
        self.i = i
        self.j = j
        self.k = k
        self.finished = False
        self.parent = parent
        self.app = parent.app

    def run(self):
        counter = 0
        # self.results = []

        camera_time_0 = None
        time_0 = None
        while not self.finished:
            print("Take image")
            # self.app.main_window.microscope_esp32_controller_serial.write("\nX3 0\n")
            # image_result =
            # #image_result = self.app.main_window.camera.camera.GetNextImage()
            # if image_result.IsIncomplete():
            #     print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
            # else:
            if True:
                x, y, z = self.parent.m_pos
                camera_timestamp = time.time()
                # camera_timestamp = image_result.GetTimeStamp()
                if not camera_time_0:
                    camera_time_0 = camera_timestamp
                if not time_0:
                    time_0 = self.parent.m_pos_t
                print("image result at", camera_timestamp - time_0, x, y, z)
                # d = np.zeros( (768,1024,3), np.uint8)
                # d = image_result.GetNDArray()
                # image_result.Release()
                fname = f"{self.parent.prefix}/test.{self.i}_{self.j}.{counter}.tif"
                # self.results.append((fname, d))
                tifffile.imwrite(fname, d)

                json.dump(
                    {
                        "fname": os.path.basename(fname),
                        "counter": counter,
                        "camera_timestamp": camera_timestamp - camera_time_0,
                        "timestamp": self.parent.m_pos_t - time_0,
                        "counter": self.counter,
                        "i": self.i,
                        "j": self.j,
                        "k": self.k,
                        "x": x,
                        "y": y,
                        "z": z,
                    },
                    self.parent.tile_config,
                )
                self.parent.tile_config.write("\n")
                self.parent.tile_config.flush()
                self.counter += 1
            time.sleep(0.6)

        self.app.main_window.microscope_esp32_controller_serial.write("P2000000 6\n")


class Acquisition:
    def __init__(self, scene, rect, lastRubberBand):
        self.app = QtWidgets.QApplication.instance()
        self.scene = scene
        self.rect = rect
        self.lastRubberBand = lastRubberBand
        self.startPos = QtCore.QPointF(
            self.lastRubberBand[0].x(), self.lastRubberBand[0].y()
        )
        self.grid = []
        self.counter = 0

        self.start_time = time.time()

        # self.prefix = os.path.join("movie", str(self.start_time))
        # os.makedirs(self.prefix)
        self.prefix = os.path.join("photo", str(self.start_time))
        os.makedirs(self.prefix)

        self.orig_grid = self.generateGrid(*self.lastRubberBand)

        self.tile_config = open(os.path.join(self.prefix, "tile_config.json"), "w")
        self.inner_counter = 0
        self.block = None

        self.app.main_window.camera.snapshotCompleted.connect(self.snapshotCompleted)

        # self.app.main_window.camera.imageChanged.connect(self.imageChanged)
        self.out = None
        self.fname = None
        self.vs = []

    def snapshotCompleted(self, image):
        pos = self.app.main_window.m_pos
        self.app.main_window.tile_graphics_view.scene().addImage(
            image, pos
        )
        # format = QtGui.QImage.Format.Format_RGB888
        # s = frame.shape
        # image = QtGui.QImage(frame, s[1], s[0], format)
        image = image.mirrored(horizontal=True, vertical=False)
        t = str(time.time())
        filename = f"{self.prefix}/test.{t}.png"
        image.save(filename)
        pixmap = QtGui.QPixmap.fromImage(image)
        # self.image_view.setFixedSize(1440/2, 1080/2)
        self.app.main_window.image_view.setPixmap(pixmap)

        json.dump(
            {
                "fname": os.path.basename(filename),
                "counter": self.counter,
                # "camera_timestamp": camera_timestamp-camera_time_0,
                "timestamp": t,
                "i": self.i,
                "j": self.j,
                "k": self.k,
                "x": self.x,
                "y": self.y,
                "z": self.z,
                "stage_x": pos[0],
                "stage_y": pos[1],
                "stage_z": pos[2],
            },
            self.tile_config,
        )
        self.counter += 1
        self.tile_config.write("\n")
        self.tile_config.flush()

        self.doCmd()

    def generateGrid(self, from_, to):
        grid = []
        # self.zs = [-0.2,-0.1,0,0.1,0.2]
        self.zs = [0]

        self.x_min = from_.x() * PIXEL_SCALE
        self.y_min = from_.y() * PIXEL_SCALE
        self.x_max = to.x() * PIXEL_SCALE
        self.y_max = to.y() * PIXEL_SCALE
        self.z_min = self.zs[0]
        self.z_max = self.zs[-1]
        # print("x min to max", self.x_min, self.x_max)
        # print("y min to max", self.y_min, self.y_max)
        # print("fov_x", FOV_X)
        # print("fov_y", FOV_Y)
        z = self.app.main_window.m_pos[2]
        num_z = len(self.zs)
        self.ys = np.arange(self.y_min, self.y_max, FOV_Y * (9 / 10))
        # ys = [y_min, y_max]
        num_y = len(self.ys)
        self.xs = np.arange(self.x_min, self.x_max, FOV_X * (9 / 10))
        # self.xs = [self.x_min, self.x_max]
        num_x = len(self.xs)

        # print(self.xs)
        # print(self.ys)
        for i, deltaz in enumerate(self.zs):
            curr_z = z + deltaz

            for k, gx in enumerate(self.xs):
                for j, gy in enumerate(self.ys):
                # if j % 2 == 0:
                #xs = enumerate(self.xs)
                # else:
                #     print(xs)

                #     xs = enumerate(reversed(self.xs))
                #     print(xs)
                    grid.append(
                        [
                            ["MOVE_TO", (float(gx), float(gy), curr_z), (k, j, 0), 50],
                            ["WAIT"],
                            ["PHOTO"],
                        ]
                    )
                # inner_grid = []
                # inner_grid.append(["MOVE_TO", (self.xs[0],gy,curr_z), (i,j,0), 100])
                # inner_grid.append(["WAIT"])
                # inner_grid.append(["START_TRIGGER", (i, j, 0)])
                # inner_grid.append(["MOVE_TO", (self.xs[1],gy,curr_z), (i,j,1), 50])
                # inner_grid.append(["WAIT"])
                # inner_grid.append(["END_TRIGGER"])
                # grid.append(inner_grid)

        grid.append([["DONE"]])

        with open(os.path.join(self.prefix, "scan_config.json"), "w") as scan_config:
            json.dump(
                {
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
                },
                scan_config,
            )
        # print("grid:", grid)
        return grid

    def startAcquisition(self):
        self.grid = self.orig_grid[:]
        self.app.main_window.serial.stateChanged.connect(self.acq)
        self.app.main_window.serial.messageChanged.connect(self.output)
        self.m_pos_ts = []
        self.app.main_window.serial.posChanged.connect(self.pos)
        self.app.main_window.camera.disableCallback()
        self.time_0 = time.time()
        self.counter = 0

        self.doCmd()
        # print("cmd=", cmd)
        # self.app.main_window.label_counter.setText(str(self.counter))

    def pos(self, x, y, z, t):
        # print("x, y, z, t", x, y, z, t)
        self.m_pos = x, y, z
        self.m_pos_t = t
        self.m_pos_ts.append((self.m_pos, t))

    def doCmd(self):
        print("doCmd", self.block)
        if self.block is None or self.block == []:
            self.block = self.grid.pop(0)
        # print("self.block: ", self.block)

        subcmd = self.block.pop(0)

        self.cur = subcmd
        print("Subcmd", subcmd[0])
        if subcmd[0] == "HOME_X":
            g = f"$HX\n"
            self.app.main_window.serial.write(g)
        elif subcmd[0] == "HOME_Y":
            g = f"$HY\n"
            self.app.main_window.serial.write(g)
        elif subcmd[0] == "MOVE_TO":
            self.x, self.y, self.z = subcmd[1]
            self.k, self.j, self.i = subcmd[2]
            f = subcmd[3]
            pos = self.app.main_window.m_pos
            if pos[0] == self.x and pos[1] == self.y and pos[2] == self.z:
                print("already at position")
            else:
                g = f"G90 G21 G1 F{f} X{self.x:.3f} Y{self.y:.3f} Z{self.z:.3f}\n"
                self.app.main_window.serial.write(g)
                self.app.main_window.label_k.setText(
                    f"col {self.k+1} of {len(self.xs)}"
                )
                self.app.main_window.label_j.setText(
                    f"row {self.j+1} of {len(self.ys)}"
                )
                self.app.main_window.label_i.setText(
                    f"dep {self.i+1} of {len(self.zs)}"
                )
        elif subcmd[0] == "WAIT":
            self.app.main_window.serial.write("G4 P1\n")
        elif subcmd[0] == "PHOTO":
            self.app.main_window.camera.snapshot()
        # elif subcmd[0] == 'START_TRIGGER':
        #     i, j, k = subcmd[1]
        #     self.startTrigger(i, j, k)
        #     print("started trigger, doing next command")
        #     self.doCmd()
        # elif subcmd[0] == 'END_TRIGGER':
        #     self.endTrigger()
        #     self.doCmd()
        elif subcmd[0] == "DONE":
            self.app.main_window.tile_graphics_view.stopAcquisition()
            self.app.main_window.camera.enableCallback()
            print("DONE")
            self.tile_config.close()
            # with open(os.path.join(self.prefix, "stage_config.json"), "w") as stage_config:
            #     json.dump(self.m_pos_ts, stage_config)
        else:
            print("Unknown subcmd", subcmd)

    def output(self, output):
        print("output", output)
        if output == "ok" and self.cur[0] == "WAIT":
            # print('go to next')
            self.doCmd()

    def acq(self, state):
        print("acq", state)
        if state == "Idle" and self.cur[0] in ("MOVE_TO", "HOME_X", "HOME_Y"):
            # print("go to next")
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
