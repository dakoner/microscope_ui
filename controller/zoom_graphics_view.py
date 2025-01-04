import time
from PyQt6 import QtGui, QtCore, QtWidgets
import sys
import functools

sys.path.append("..")
from config import PIXEL_SCALE, WIDTH, HEIGHT, STAGE_X_SIZE, STAGE_Y_SIZE

from movie_acquisition import Acquisition
#from photo_acquisition import Acquisition


def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2


class ZoomGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, scene, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setScene(scene)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scene.changed.connect(self.changed)
        
    def changed(self, event):
        self.fitInView(self.scene().currentRect)#.adjusted(100, 100, 100, 100))
        
    def keyPressEvent(self, event):
        event.ignore()

    # def resizeEvent(self, *args):
    #     self.fitInView(self.scene().sceneRect())#, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
    #     return super().resizeEvent(*args)
