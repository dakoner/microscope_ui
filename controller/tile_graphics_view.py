import time
from PyQt6 import QtGui, QtCore, QtWidgets
import sys
import functools

sys.path.append("..")
from config import PIXEL_SCALE, WIDTH, HEIGHT, STAGE_X_SIZE, STAGE_Y_SIZE

from movie_acquisition import Acquisition as MovieAcquisition
from photo_acquisition import Acquisition as PhotoAcquisition


def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2


class TileGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, scene, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setScene(scene)
        self.rubberBandChanged.connect(self.onRubberBandChanged)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        #print("Scene rect:", self.scene().sceneRect(), self.scene().itemsBoundingRect())
        # self.fitInView(self.scene().itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        #self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.centerOn(self.scene().itemsBoundingRect().width()/2, self.scene().itemsBoundingRect().height()/2)
        # self.setMouseTracking(True)
        self.acquisition = None

    def keyPressEvent(self, event):
        #event.ignore()

        key = event.key()
        if key == QtCore.Qt.Key.Key_Plus:
            self.scale(1.1, 1.1)
        elif key == QtCore.Qt.Key.Key_Minus:
            self.scale(0.9, 0.9)

    def stopAcquisition(self):
        self.acquisition = None

    def resizeEvent(self, *args):
        self.fitInView(self.scene().sceneRect())#, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return super().resizeEvent(*args)

    def onRubberBandChanged(self, rect, from_, to):
        if from_.isNull() and to.isNull():
            pen = QtGui.QPen(QtCore.Qt.GlobalColor.red)
            pen.setWidth(0)
            color = QtGui.QColor(QtCore.Qt.GlobalColor.black)
            color.setAlpha(0)
            brush = QtGui.QBrush(color)

            rect = self.scene().addRect(
                self.lastRubberBand[0].x(),
                self.lastRubberBand[0].y(),
                self.lastRubberBand[1].x() - self.lastRubberBand[0].x(),
                self.lastRubberBand[1].y() - self.lastRubberBand[0].y(),
                pen=pen,
                brush=brush,
            )
            rect.setZValue(3)
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
                self.acquisition = MovieAcquisition(self.scene, rect.rect(), self.lastRubberBand)
            else:
                self.acquisition = PhotoAcquisition(self.scene, rect.rect(), self.lastRubberBand)

            self.acquisition.startAcquisition()
        else:
            self.lastRubberBand = from_, to

    def reset(self):
        self.scene().clear()
        self.addStageRect()
        self.addCurrentRect()

