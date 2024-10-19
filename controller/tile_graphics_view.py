import time
from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import functools
sys.path.append("..")
from config import PIXEL_SCALE, WIDTH, HEIGHT

#from movie_acquisition import Acquisition
from photo_acquisition import Acquisition
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

   
    # def mouseMoveEvent(self, event):mouseRele
    #     print("tile scene moved")
    #     app = QtWidgets.QApplication.instance()
    #     pos = event.scenePos()
    #     app.main_window.statusbar.showMessage(f"Canvas: {pos.x():.3f}, {pos.y():.3f}, Stage: {pos.x()*PIXEL_SCALE:.3f}, {pos.y()*PIXEL_SCALE:.3f}")
    #     print("y")
    
    # def mousePressEvent(self, event):
    #     #print("tile scene pressed")
    #     app = QtWidgets.QApplication.instance()
    #     #self.press = QtCore.QPointF(event.pos())

    def mouseReleaseEvent(self, event):
        print("mouse release event")
        if abs((event.scenePos() - event.buttonDownScenePos(QtCore.Qt.MouseButton.LeftButton)).manhattanLength()) == 0.0:
            app = QtWidgets.QApplication.instance()
            if app.main_window.state_value.text() == 'Jog':
                print('cancel jog')
                app.main_window.cancel()
            x = event.scenePos().x() - (WIDTH)
            y = event.scenePos().y() - (HEIGHT)
            app.main_window.moveTo(event.scenePos())
        event.accept()
        

class TileGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rubberBandChanged.connect(self.onRubberBandChanged)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.scene = TileGraphicsScene()
        self.setScene(self.scene)
        self.addStageRect()
        print("Scene rect:", self.scene.sceneRect(), self.scene.itemsBoundingRect())
        self.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.centerOn(self.scene.itemsBoundingRect().width()/2, self.scene.itemsBoundingRect().height()/2)

        self.currentRect = None
        self.acquisition = None


    def keyPressEvent(self, event):
        print("keyPressEvent")
        event.ignore()
    #     key = event.key()
    #     if key == QtCore.Qt.Key_Plus:
    #         self.scale(1.1, 1.1)
    #     elif key == QtCore.Qt.Key_Minus:
    #         self.scale(0.9, 0.9)   

    def addStageRect(self):
        pen = QtGui.QPen(QtCore.Qt.red)
        pen.setWidth(10)
        brush = QtGui.QBrush(QtCore.Qt.blue)
        #print(0, 0, 45/PIXEL_SCALE, 45/PIXEL_SCALE)
        self.stageRect = self.scene.addRect(0, 0, 110/PIXEL_SCALE, 83/PIXEL_SCALE, pen=pen, brush=brush)
        self.stageRect.setZValue(0)

    def addCurrentRect(self):
        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(10)
        brush = QtGui.QBrush()
        rect = QtCore.QRectF(0, 0, WIDTH, HEIGHT)
        self.currentRect = self.scene.addRect(rect, pen=pen, brush=brush)
        self.currentRect.setZValue(5)

    def updateCurrentRect(self, x, y):
        if not self.currentRect:
            self.addCurrentRect()
        self.currentRect.setPos(x/PIXEL_SCALE, y/PIXEL_SCALE)
        self.centerOn(self.currentRect)
    
    # def doAcquisition(self):
    #     if self.acquisition:
    #         self.acquisition.doAcquisition()

    def stopAcquisition(self):
        self.acquisition = None

    def resizeEvent(self, *args):
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        return super().resizeEvent(*args)


    def onRubberBandChanged(self, rect, from_ , to):
        if from_.isNull() and to.isNull():    
            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(10)
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
        self.addStageRect()
        self.addCurrentRect()
    

    def addImageIfMissing(self, draw_data, pos):
        if self.acquisition:
            print("Not adding image during acquisition")
            return
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
        if a > 500000:
            #print("Adding")
            self.addImage(draw_data, pos)
            
    def addImage(self, draw_data, pos):
            #print('addImage')
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
            image = image.mirrored(horizontal=True, vertical=False)

            pixmap = QtGui.QPixmap.fromImage(image)
            pm = self.scene.addPixmap(pixmap)
            pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
            pm.setZValue(1)
       
