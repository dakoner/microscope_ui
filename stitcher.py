import json
import sys
sys.path.append("..")
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import os


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
    print(len(results))
    return results


class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        results = parse("z:\\src\\microscope_ui\\movie\\TileConfiguration.txt")

        for filename, coords in results:
            if not os.path.exists(filename):
                print("Could not locate", filename)
            else:
                i = QtGui.QImage(filename)
                p = QtGui.QPixmap(i)
                item = self.addPixmap(p)
                item.setPos(*coords)


class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.scene = Scene()
        self.setScene(self.scene)
        
        self.fitInView(self.scene.sceneRect())

class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)

        self.tile_window = TileWindow()
        self.tile_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.exec_()