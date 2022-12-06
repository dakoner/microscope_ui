import time
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

class TileGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName("TileGraphicsScene")

    def mouseMoveEvent(self, event):
        #print("tile scene moved")
        app = QtWidgets.QApplication.instance()
        pos = event.pos()
        app.main_window.statusbar.showMessage(f"Canvas: {pos.x():.3f}, {pos.y():.3f}, Stage: {pos.x()*PIXEL_SCALE:.3f}, {pos.y()*PIXEL_SCALE:.3f}")
    
    # def mousePressEvent(self, event):
    #     #print("tile scene pressed")
    #     app = QtWidgets.QApplication.instance()
    #     #self.press = QtCore.QPointF(event.pos())

    def mouseReleaseEvent(self, event):
        if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
            print('control pressed')
            if abs((event.scenePos() - event.buttonDownScenePos(QtCore.Qt.MouseButton.LeftButton)).manhattanLength()) == 0.0:
                app = QtWidgets.QApplication.instance()
                if app.main_window.state_value.text() == 'Jog':
                    print('cancel jog')
                    app.main_window.cancel()
                app.main_window.moveTo(event.scenePos())
        else:
            print("rubber")
        

class TileGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rubberBandChanged.connect(self.onRubberBandChanged)


        self.scene = TileGraphicsScene()
        self.setScene(self.scene)
        self.addStageRect()

        self.currentRect = None
        

        
        self.acquisition = None



    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Plus:
            self.scale(1.1, 1.1)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.9, 0.9)   

    def addStageRect(self):
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidth(100)
        brush = QtGui.QBrush()
        self.stageRect = self.scene.addRect(0, 0, 65/PIXEL_SCALE, 85/PIXEL_SCALE, pen=pen, brush=brush)
        self.stageRect.setZValue(0)

    def addCurrentRect(self):
        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(200)
        brush = QtGui.QBrush()
        rect = QtCore.QRectF(0, 0, WIDTH, HEIGHT)
        self.currentRect = self.scene.addRect(rect, pen=pen, brush=brush)
        self.currentRect.setZValue(5)

    def updateCurrentRect(self, x, y):
        if not self.currentRect:
            self.addCurrentRect()
        self.currentRect.setPos(x/PIXEL_SCALE, y/PIXEL_SCALE)
        self.centerOn(self.currentRect)
    
    def doAcquisition(self):
        if self.acquisition:
            self.acquisition.doAcquisition()

    def stopAcquisition(self):
        self.acquisition = None

    # def resizeEvent(self, *args):
    #     self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

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
            self.acquisition = Acquisition(self.lastRubberBand)
            self.acquisition.startAcquisition()
        else:
            self.lastRubberBand = from_, to
    def reset(self):
        self.scene.clear()
        #self.addStageRect()
        #self.adddCurrentRect()
    # def mouseMoved(self, event):
    #     print("tile view moved")

    # def mousePressed(self, event):
    #     print("tile view pressed")
    # def mouseReleased(self, event):
    #     print("tile view released")

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
        if a > 10000:
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_Grayscale8)
            pixmap = QtGui.QPixmap.fromImage(image)
            print("add pixmap")
            pm = self.scene.addPixmap(pixmap)
            pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
            pm.setZValue(1)
       