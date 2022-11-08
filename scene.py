from PyQt5 import QtWidgets, QtCore, QtGui
from config import WIDTH, HEIGHT, PIXEL_SCALE

class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, app, *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)

        pen_color = QtGui.QColor(QtCore.Qt.blue)
        pen = QtGui.QPen(pen_color)
        pen.setWidth(20)
        
        brush_color = QtGui.QColor(QtCore.Qt.blue)
        brush_color.setAlpha(15)
        brush = QtGui.QBrush(brush_color)
        self.borderRect = self.addRect(0, 0, 60/PIXEL_SCALE, 60/PIXEL_SCALE, pen=pen, brush=brush)
        self.borderRect.setZValue(255)


        pen = QtGui.QPen()
        pen.setWidth(20)
        color = QtGui.QColor(QtCore.Qt.red)
        #color.setAlpha(1)
        brush = QtGui.QBrush(color)
        self.currentRect = self.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(20)

        color = QtGui.QColor(25, 25, 25)
        brush = QtGui.QBrush(color)
        self.slideRect = self.addRect(0, 25.8/PIXEL_SCALE, 60/PIXEL_SCALE, 20/PIXEL_SCALE, brush=brush)
        self.slideRect.setZValue(1)


        self.pixmap = self.addPixmap(QtGui.QPixmap())
        self.pixmap.setZValue(4)

        self.setSceneRect(0, 0, 60/PIXEL_SCALE, 60/PIXEL_SCALE)

    def mouseMoveEvent(self, event):
        self.app.main_window.statusBar().showMessage(f"Canvas: {event.scenePos().x():.3f}, {event.scenePos().y():.3f}, Stage: {event.scenePos().x()*PIXEL_SCALE:.3f}, {event.scenePos().y()*PIXEL_SCALE:.3f}")
        return super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        #print("mouse press")
        self.press = event.scenePos()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        print("mouse release")
        if (self.press - event.scenePos()).manhattanLength() == 0.0:
            self.app.moveTo(self.press)
        else:
            self.app.generateGrid(self.press, event.scenePos())
        return super().mouseReleaseEvent(event)


