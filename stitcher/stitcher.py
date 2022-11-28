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
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.


class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def keyPressEvent(self, event):
        key = event.key()  
        if key == QtCore.Qt.Key_Plus:
            self.scale(1.1, 1.1)
            event.accept()
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.9,0.9)
            event.accept()
        return super().keyPressEvent(event)

    def mousePressEvent(self, event):
        print("mouse press", event.buttons())
        if event.buttons() & QtCore.Qt.RightButton:
            self.press = event.pos()

    def mouseReleaseEvent(self, event):
        print("mouse release", event.buttons())
        if event.buttons() & QtCore.Qt.RightButton:
            delta = event.pos() - self.press
            if delta.y() > -10:
                scale = 1.01**delta.y()
                print("delta", delta.y(), "scale", scale)
                self.scale(scale, scale)
        self.press = None

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.RightButton:
            delta = event.pos() - self.press
            if delta.y() > -10:
                scale = 1.01**delta.y()
                print("delta", delta.y(), "scale", scale)
                #self.scale(scale, scale)
       
    def resizeEvent(self, event):
    #     pass
        #print("tile window resizeEvent")
        self.fitInView(self.scene().sceneRect(), QtCore.Qt.KeepAspectRatio)
        #self.scale(2,2)
        #event.accept()
        return super().resizeEvent(event)

class TabLoader(QtCore.QThread):
    messageSignal = QtCore.pyqtSignal(list, str)

    def __init__(self, prefix, r, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = prefix
        self.r = r



    def run(self):
        for t in self.r.counter.unique()[:-1]:
            # print(t)
            # Get all items in time t
            d = self.r[self.r.counter == t]
            result = []
            for row in d.itertuples():
                fname = os.path.join(self.prefix, row.fname)
                print(row)
                if row.k == 0:
                    continue
                x0 = row.k * FOV_X_PIXELS
                y0 = row.j * FOV_Y_PIXELS
                image = QtGui.QImage(fname)
                result.append([image, x0, y0])
            self.messageSignal.emit(result, str(t))
                
            

class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        g = glob.glob("movie/*")
        g.sort()
        prefix = g[-1]
        d=json.load(open(f"{prefix}/scan_config.json"))
        r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
        r.set_index(['counter', 'i', 'j', 'k'])


        self.tab_loader = TabLoader(prefix, r, self)
        self.tab_loader.messageSignal.connect(self.onTabLoaded)
        self.tab_loader.start()

    def onTabLoaded(self, images, label):
        scene = QtWidgets.QGraphicsScene()
        for image, x0, y0 in images:
            pixmap = QtGui.QPixmap(image)
            item = scene.addPixmap(pixmap)
            item.setPos(x0, y0)
            
        tw = TileWindow()
        tw.setScene(scene)
        tw.setSceneRect(scene.sceneRect())
        self.addTab(tw, label)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("stitcher/stitcher.ui", self)
                
class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)

        self.main_window = MainWindow()
        self.main_window.show()
   
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()