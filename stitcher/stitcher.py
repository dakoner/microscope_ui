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



class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def addResults(self, prefix, d):
        counter = 0
        for row in d.itertuples():
            fname = os.path.join(prefix, row.fname)
            if row.k == 0:
                continue
            x0 = row.k * FOV_X_PIXELS
            y0 = row.j * FOV_Y_PIXELS
            image = QtGui.QImage(fname)
            pixmap = QtGui.QPixmap(image)
            item = self.addPixmap(pixmap)
            item.setPos(x0, y0)


    # def resizeEvent(self, event):
    #     print("scene resize")

class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, prefix, results, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = Scene()
        self.scene.addResults(prefix, results)
        self.setScene(self.scene)

        self.setMouseTracking(True)
        #self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        #self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        #self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)


        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.setSceneRect(self.scene.sceneRect())
        #r = self.scene.itemsBoundingRect()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def keyPressEvent(self, event):
        print("tile graphics view key press event")
        key = event.key()  
        if key == QtCore.Qt.Key_Plus:
            self.scale(2, 2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.5, 0.5)
        return super().keyPressEvent(event)

    # def mousePressEvent(self, event):
    #     print("mouse press", event.buttons())
    #     self.press = event.pos()

    # def mouseReleaseEvent(self, event):
    #     print("mouse release", event.buttons())

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
    #    self.press = None

    # def mouseMoveEvent(self, event):
    #     # if event.buttons() & QtCore.Qt.RightButton:
    #     #     delta = event.pos() - self.press
    #     #     if delta.y() > -10:
    #     #         scale = 1.01**delta.y()
    #     #         print("delta", delta.y(), "scale", scale)
    #     #         self.scale(scale, scale)
    #     if event.buttons() & QtCore.Qt.LeftButton:
    #         print("mouse moved while left button pressed")
    #         delta = event.pos() - self.press
    #         print("delta", delta)
    #         self.translate(delta.x(), delta.y())
    #         #self.translate(1, 1)
    #         #event.accept()


    def resizeEvent(self, event):
        print("tile window resizeEvent")
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        #self.scale(2,2)
        #event.accept()


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        g = glob.glob("movie/*")
        g.sort()
        prefix = g[-1]
        d=json.load(open(f"{prefix}/scan_config.json"))
        r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
        r.set_index(['counter', 'i', 'j', 'k'])

        for t in r.counter.unique()[:-1]:
            # print(t)
            # Get all items in time t
            d = r[r.counter == t]


            w = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            w.setLayout(layout)
            tw = TileWindow(prefix, d)
            layout.addWidget(tw)
            self.addTab(w, str(t))


        self.dumpObjectTree()


    def resizeEvent(self, event):
        print("tab widget resizeEvent")
        return super().resizeEvent(event)


class CentralWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("central widget")
        
    def resizeEvent(self, event):
        print("central widget resizeEvent")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("stitcher/stitcher.ui", self)
        self.setCentralWidget(self.centralwidget)
                
        
    def resizeEvent(self, event):
        print("main window  resize event")
        self.centralWidget().resizeEvent(event)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)

        self.main_window = MainWindow()
        self.main_window.showMaximized()
        self.installEventFilter(self)

    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            self.main_window.tabWidget.currentWidget().keyPressEvent(event)
        return False

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()