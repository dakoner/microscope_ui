from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import functools
sys.path.append("..")
from microscope_ui.config import PIXEL_SCALE, WIDTH, HEIGHT

from acquisition import Acquisition
def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2

class TileScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseMoveEvent(self, event):
        app = QtWidgets.QApplication.instance()
        app.main_window.statusbar.showMessage(f"Canvas: {event.scenePos().x():.3f}, {event.scenePos().y():.3f}, Stage: {event.scenePos().x()*PIXEL_SCALE:.3f}, {event.scenePos().y()*PIXEL_SCALE:.3f}")
        return super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self.press = event.scenePos()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        app = QtWidgets.QApplication.instance()
        if (self.press - event.scenePos()).manhattanLength() == 0.0:
            if app.main_window.state_value.text() == 'Jog':
                app.cancel()
                self.timer = QtCore.QTimer()
                p = functools.partial(app.moveTo, self.press)
                self.timer.timeout.connect(p)
                self.timer.setSingleShot(True)
                self.timer.start(100)
            else:
                app.moveTo(self.press)
        return super().mouseReleaseEvent(event)

class TileGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.graphicsView.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.setMouseTracking(True)
        self.rubberBandChanged.connect(self.onRubberBandChanged)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)


        self.scene = TileScene()
        self.setScene(self.scene)

        pen = QtGui.QPen()
        pen.setWidth(1)
        color = QtGui.QColor()
        brush = QtGui.QBrush(color)
        self.stageRect = self.scene.addRect(0, 0, 40/PIXEL_SCALE, 85/PIXEL_SCALE, pen=pen, brush=brush)
        self.stageRect.setZValue(0)

        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(50)
        brush = QtGui.QBrush()
        self.currentRect = self.scene.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(5)

        self.scene.setSceneRect(self.stageRect.boundingRect())
        self.setSceneRect(self.stageRect.boundingRect())
        self.acquisition = None

    def doAcquisition(self):
        if self.acquisition:
            self.acquisition.doAcquisition()

    def stopAcquisition(self):
        self.acquisition.grid = []
        self.acquisition.orig_grid = []


    def resizeEvent(self, *args):
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def onRubberBandChanged(self, rect, from_ , to):
        if from_.isNull() and to.isNull():    
            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(50)
            color = QtGui.QColor(QtCore.Qt.black)
            color.setAlpha(0)
            brush = QtGui.QBrush(color)
            
            rect = self.scene.addRect(
                self.lastRubberBand[0].x(), self.lastRubberBand[0].y(),
                self.lastRubberBand[1].x()-self.lastRubberBand[0].x(), 
                self.lastRubberBand[1].y()-self.lastRubberBand[0].y(),
                pen=pen, brush=brush)
            rect.setZValue(3)
            
            QtWidgets.QApplication.instance().cancel()
            self.acquisition = Acquisition(self.lastRubberBand)
            self.acquisition.startAcquisition()
        else:
            self.lastRubberBand = from_, to


    def addImageIfMissing(self, draw_data, pos):
        #if not self.acquisition or len(self.acquisition.grid) == 0:
        #    return
        ci = self.currentRect.collidingItems()
        # Get the qpainterpath corresponding to the current image location, minus any overlapping images
        qp = QtGui.QPainterPath()
        qp.addRect(self.currentRect.sceneBoundingRect())
        qp2 = QtGui.QPainterPath()
        for item in ci:
            if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                qp2.addRect(item.sceneBoundingRect())

        qp3 = qp.subtracted(qp2)
        p = qp3.toFillPolygon()
        a = calculate_area(p)
        if a > 200000:
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(image)
            pm = self.scene.addPixmap(pixmap)
            pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
            pm.setZValue(1)
       