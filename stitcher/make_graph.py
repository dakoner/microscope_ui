import sys

sys.path.insert(0, "controller")
import tifffile
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
from PyQt6 import QtGui, QtCore, QtWidgets
import imageio as iio

sys.path.insert(0, "controller")
sys.path.insert(0, "../controller")
from config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE
from PIL import Image


class ImageNode(QtWidgets.QGraphicsPixmapItem):
    def __init__(self, bounds, fname, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlags(
            QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsMovable
           # | QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        x, y = bounds[0], bounds[1]
        # width, height = bounds[2] - x, bounds[3] - y
        image = iio.imread(fname)
        alpha = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
        alpha.fill(255)
        image = np.dstack((image, alpha))
        image = qimage2ndarray.array2qimage(image)  # , normalize=True)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.setPixmap(pixmap)
        self.edges = []
        self.setPos(x, y)

    def paint(self, painter, opt, widget=None):
        colliding = [item for item in self.collidingItems() if item is not self and isinstance(item, ImageNode)]
        if not colliding:
            return super().paint(painter, opt, widget)

        painter.save()

        collisions = QtGui.QPolygonF()

        for other in colliding:
            collisions = collisions.united(
                other.mapToScene(other.boundingRect()))
        collisionPath = QtGui.QPainterPath()
        collisionPath.addPolygon(collisions)
        
        fullPath = QtGui.QPainterPath()
        fullPath.addPolygon(self.mapToScene(self.boundingRect()))
        # draw the pixmap only where it has no colliding items
        painter.setClipPath(self.mapFromScene(fullPath.subtracted(collisionPath)))
        super().paint(painter, opt, widget)
        # draw the collision parts with half opacity
        painter.setClipPath(self.mapFromScene(fullPath.intersected(collisionPath)))
        painter.setOpacity(.5)
        super().paint(painter, opt, widget)
        
        
        painter.restore()

        painter.save()        
        painter.setOpacity(1)
        painter.setClipping(False)
        
        border_colour = QtGui.QColor(241, 175, 0, 255)
        painter.setPen(QtGui.QPen(border_colour, 2))
        painter.drawPath(self.mapFromScene(fullPath.intersected(collisionPath)))
        
        
        border_colour = QtGui.QColor(175, 241, 0, 255)
        painter.setPen(QtGui.QPen(border_colour, 2))
        painter.drawPath(self.mapFromScene(fullPath.subtracted(collisionPath)))
        painter.restore()
        
        return #super().paint(painter, opt, widget)
        
    def itemChange(self, change, variant):
        if change == QtWidgets.QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            t = variant - self.pos()
            for edge in self.edges:
                l = edge.line()
                if edge.polys[0] == self:
                    l.setP1(l.p1() + t)
                    edge.setLine(l)
                elif edge.polys[1] == self:
                    l.setP2(l.p2() + t)
                    edge.setLine(l)
        return super().itemChange(change, variant)


class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheModeFlag.CacheNone)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        #self.setStyleSheet("background-color: transparent;")

        self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        # self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
    
    def keyPressEvent(self, event):
        key = event.key()
        # check if autorepeat (only if doing cancelling-moves)
        if key == QtCore.Qt.Key.Key_Up:
            print("Scale")
            self.scale(2, 2)
        elif key == QtCore.Qt.Key.Key_Down:
            self.scale(0.5, 0.5)
        elif key == QtCore.Qt.Key.Key_S:
            r = self.scene.itemsBoundingRect()
            width = round(r.width())
            height = round(r.height())
            image = QtGui.QImage(width, height, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
            p = QtGui.QPainter(image)
            self.scene.render(p)
            p.end()
            fname = "image.png"
            image.save(fname)
            #image = qimage2ndarray.byte_view(image)  # , normalize=True)
            #image.save()
            #tifffile.imwrite(fname, image)
    # def resizeEvent(self, event):
    #     # fitInView interferes with scale()
    #     self.fitInView(self.scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)

    def addItem(self, bounds, fname):

        r = ImageNode(bounds, fname)
        self.scene.addItem(r)

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
        self.tc.load(f"{prefix}/images.origin.txt")
        #self.tc.load(f"{prefix}/TileConfiguration.registered.registered.txt")
        
        self.tc.move_to_origin()
        self.create_graph()
        self.create_scene()

        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setCentralWidget(self.scanned_image)
        self.scanned_image.show()
        # self.scanned_image.scene.setSceneRect(
        #     self.scanned_image.scene.itemsBoundingRect()
        # )
        self.scanned_image.scene.clearSelection()

        self.main_window.show()#Maximized()

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
            fname = self.graph.nodes[node]["fname"]
            poly_to_item[node] = self.scanned_image.addItem(
                node.bounds, self.prefix / fname
            )

        # for edge in self.graph.edges:
        #     line = self.scanned_image.addEdge(edge)
        #     i1 = poly_to_item[edge[0]]
        #     i1.edges.append(line)
        #     i2 = poly_to_item[edge[1]]
        #     i2.edges.append(line)
        #     line.polys = (i1, i2)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prefix = r"C:\Users\davidek\microscope_ui\controller\photo\1732319758.459453"
    else:
        prefix = sys.argv[1]

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(prefix)
    app.exec()
