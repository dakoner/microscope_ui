import glob
import json
import sys
sys.path.append("..")
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import os
from PyQt5.uic import loadUi


def parse(filename):
    results = []
    f = open(filename)
    l = f.readlines()
    for i in range(len(l)):
        line = l[i]
        if line[0] == '#':
            continue
        elif line.startswith("dim="):
            continue
        elif line == '\n':
            continue
        else: # possibly an image line
            try:
                image_filename, _, coords = line.split(";")
            except ValueError:
                print("Failed to parse", line)
            else:
                dir_ = os.path.dirname(filename)
                fname = os.path.join(dir_, image_filename)
               
                results.append((fname, eval(coords)))
    return results


class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        

    def addResults(self, results):
        for filename, coords in results:
            if not os.path.exists(filename):
                print("Could not locate", filename)
            else:
                i = QtGui.QImage(filename)
                p = QtGui.QPixmap(i)
                item = self.addPixmap(p)
                item.setPos(coords[0], coords[1])

class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, results, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.scene = Scene()
        self.scene.addResults(results)

        self.setScene(self.scene)

        self.setMouseTracking(True)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)


        r = self.scene.sceneRect()
        self.fitInView(r, QtCore.Qt.KeepAspectRatio)
        self.scale(2,2)

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
            #self.translate(delta.x(), delta.y())
            self.translate(1, 1)
            #event.accept()


    def resizeEvent(self, event):
        print("tile window resizeEvent")
        #self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        #self.scale(2,2)
        event.accept()


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("custom tab widget")


    def resizeEvent(self, event):
        print("tab widget resizeEvent")



class CentralWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("central widget")
        print("findChild", self.findChild(QtWidgets.QTabWidget))


    def resizeEvent(self, event):
        print("central widget resizeEvent")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("stitcher.ui", self)
        print(self.dumpObjectTree())
        #self.run()
        self.setCentralWidget(self.centralwidget)
        self.run()

    def run(self):
        g = glob.glob(sys.argv[1])
        g.sort(key=lambda x: int(os.path.basename(x)))
        for f in g[:1]:
            results = parse(f"{f}\\TileConfiguration.txt")
            #print(results)
            tile_window = TileWindow(results)
            label = os.path.basename(f)
            self.tabWidget.addTab(tile_window, label)
            self.tabWidget.show()


    def resizeEvent(self, event):
        print("main window  resize event")
        self.centralWidget().resizeEvent(event)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)


        self.main_window = MainWindow()
        self.main_window.show()





if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()