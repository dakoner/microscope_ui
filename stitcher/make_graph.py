import sys

sys.path.insert(0, "controller")
import shapely.geometry, shapely.strtree
from tile_configuration import TileConfiguration
import networkx as nx
import shapely
from util import tile_config_to_shapely, polys_to_intersections


import sys
import concurrent.futures
import pathlib
from tile_configuration import TileConfiguration
import os
import glob
import qimage2ndarray
import numpy as np
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets

sys.path.insert(0, "controller")
sys.path.insert(0, "../controller")
from config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE
from PIL import Image


class ImageNode(QtWidgets.QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges)
        self.edges = []
        
    def itemChange(self, change, variant):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            t = variant - self.pos()
            for edge in self.edges:
                if edge.polys[0] == self: 
                    l = edge.line()
                    l.setP1(l.p1() + t)
                    edge.setLine(l)
                elif edge.polys[1] == self:
                    l = edge.line()
                    l.setP2(l.p2() + t)
                    edge.setLine(l)
        return super().itemChange(change, variant)
        
class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)

    def resizeEvent(self, event):
        # fitInView interferes with scale()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def addItem(self, bounds):
        x, y = bounds[0], bounds[1]
        width, height = bounds[2] - x, bounds[3] - y
        r = ImageNode(0, 0, width, height)
        self.scene.addItem(r)
        r.setPos(x, y)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(10)
        r.setPen(pen)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 0))
        r.setBrush(brush)
        return r


    def addEdge(self, intersection):
        p1, p2 = intersection
        c1 = shapely.centroid(p1)
        c2 = shapely.centroid(p2)
        line = self.scene.addLine(c1.x, c1.y, c2.x, c2.y)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(10)
        line.setPen(pen)
        return line


class QApplication(QtWidgets.QApplication):
    def __init__(self, prefix, *argv):
        super().__init__(["foo"])
        self.scanned_image = ScannedImage()

        self.prefix = prefix
        self.tc = TileConfiguration()
        self.tc.load(f"{prefix}/TileConfiguration.txt")
        self.tc.move_to_origin()
        self.create_graph()
        self.create_scene()
        
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setCentralWidget(self.scanned_image)
        self.scanned_image.show()
        self.scanned_image.scene.setSceneRect(
            self.scanned_image.scene.itemsBoundingRect()
        )
        self.scanned_image.scene.clearSelection()

        self.main_window.showMaximized()

    def create_graph(self):
        polys, poly_to_fname = tile_config_to_shapely(self.prefix, self.tc)
        self.graph = nx.Graph()
        for poly in polys:
            self.graph.add_node(poly, fname=poly_to_fname[poly])
        intersections = polys_to_intersections(polys)
        for intersection in intersections:
            self.graph.add_edge(*intersection)

    def create_scene(self):
        poly_to_item = {}

        for node in self.graph.nodes:
            self.graph.add_node(node)
            poly_to_item[node] = self.scanned_image.addItem(node.bounds)
        
        for edge in self.graph.edges:
            line = self.scanned_image.addEdge(edge)
            i1 = poly_to_item[edge[0]]
            i1.edges.append(line)
            i2 = poly_to_item[edge[1]]
            i2.edges.append(line)
            line.polys = (i1, i2)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prefix = r"C:\Users\davidek\microscope_ui\controller\photo\1732319758.459453"
    else:
        prefix = sys.argv[1]

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(prefix)
    app.exec()

