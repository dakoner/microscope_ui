import pandas as pd
import tifffile
import numpy as np
import glob
import json
import sys
sys.path.append("..")
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import os
from PyQt5.uic import loadUi
from config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.



class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def addResults(self, d):

        #o = np.zeros(shape=(z_max, y_max, x_max, c_max), dtype=np.ubyte)

        # We now have all the ZYXC data for a time
        for row in d.itertuples():
            fname = row.fname
            #data = tifffile.imread(f"{prefix}/{row.fname}")
            x0 = row.gx * FOV_X_PIXELS
            y0 = row.gy * FOV_Y_PIXELS
            i = QtGui.QImage(fname)
            p = QtGui.QPixmap(i)
            item = self.addPixmap(p)
            item.setPos(x0, y0)

    def resizeEvent(self, event):
        print("scene resize")

class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, results, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("tile window")
        self.scene = Scene()
        self.scene.addResults(results)

        self.setScene(self.scene)

        self.setMouseTracking(True)
        #self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        #self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)


        #r = self.scene.sceneRect()
        #self.fitInView(r, QtCore.Qt.KeepAspectRatio)
        #self.scale(2,2)

    def mousePressEvent(self, event):
        print("mouse press", event.buttons())
        self.press = event.pos()

    def mouseReleaseEvent(self, event):
        print("mouse release", event.buttons())

        # if event.buttons() & QtCore.Qt.LeftButton:
        #     delta = event.pos() - self.press
        #     print("delta", delta)
        #     self.translate(delta.x(), delta.y())
        # elif event.buttons() & QtCore.Qt.RightButton:
        #     delta = event.pos() - self.press
        #     if delta.y() > -10:
        #         scale = 1.01**delta.y()
        #         print("delta", delta.y(), "scale", scale)
        #         self.scale(scale, scale)
        self.press = None

    def mouseMoveEvent(self, event):
        # if event.buttons() & QtCore.Qt.RightButton:
        #     delta = event.pos() - self.press
        #     if delta.y() > -10:
        #         scale = 1.01**delta.y()
        #         print("delta", delta.y(), "scale", scale)
        #         self.scale(scale, scale)
        if event.buttons() & QtCore.Qt.LeftButton:
            print("mouse moved while left button pressed")
            delta = event.pos() - self.press
            print("delta", delta)
            self.translate(delta.x(), delta.y())
            #self.translate(1, 1)
            #event.accept()


    def resizeEvent(self, event):
        print("tile window resizeEvent")
        #self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        #self.scale(2,2)
        #event.accept()


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("custom tab widget")

        prefix = "z:\\src\\microscope_ui"
        r = pd.read_json(f"{prefix}\\movie\\1668311323\\tile_config.json", lines=True)
        r.set_index(['acquisition_counter', 'gx', 'gy', 'gz'])
        t_max = len(r.acquisition_counter.unique())
        z_max = len(r.gz.unique())
        x_max = r.gx.max()*FOV_X_PIXELS+WIDTH
        y_max = r.gy.max()*FOV_Y_PIXELS+HEIGHT
        c_max = 3 
        for t in r.acquisition_counter.unique():
            print(t)
            # Get all items in time t
            d = r[r.acquisition_counter == t]

            self.addTab(TileWindow(d), str(t))



    def resizeEvent(self, event):
        print("tab widget resizeEvent")



class CentralWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("central widget")
        
    def resizeEvent(self, event):
        print("central widget resizeEvent")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("stitcher.ui", self)
        self.setCentralWidget(self.centralwidget)
                
        
    def resizeEvent(self, event):
        print("main window  resize event")
        self.centralWidget().resizeEvent(event)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)




        self.main_window = MainWindow()
        self.main_window.show()
        #self.main_window.dumpObjectTree()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()