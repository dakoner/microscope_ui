from PyQt5 import QtWidgets, QtCore, QtGui
from config import WIDTH, HEIGHT, PIXEL_SCALE

class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)
        self.setSceneRect(0, -75/PIXEL_SCALE, 75/PIXEL_SCALE, 75/PIXEL_SCALE)

        pen = QtGui.QPen()
        pen.setWidth(20)
        color = QtGui.QColor(255, 0, 0)
        #color.setAlpha(1)
        brush = QtGui.QBrush(color)
        self.currentRect = self.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(10)

        color = QtGui.QColor(25, 50, 25)
        brush = QtGui.QBrush(color)
        self.slideRect = self.addRect(0, -50/PIXEL_SCALE, 76/PIXEL_SCALE, 25+26/PIXEL_SCALE, brush=brush)
        self.slideRect.setZValue(1)


        self.pixmap = self.addPixmap(QtGui.QPixmap())
        self.pixmap.setZValue(4)


    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        print("at stage pos", event.scenePos().x()*PIXEL_SCALE, event.scenePos().y()*PIXEL_SCALE)
        self.press = event.scenePos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.app.generateGrid(self.press, event.scenePos())
        super().mouseMoveEvent(event)
