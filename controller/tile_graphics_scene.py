import time
from PyQt6 import QtGui, QtCore, QtWidgets
import sys

sys.path.append("..")
from config import PIXEL_SCALE, WIDTH, HEIGHT, STAGE_X_SIZE, STAGE_Y_SIZE



def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2


class TileGraphicsScene(QtWidgets.QGraphicsScene):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window
        self.setObjectName("TileGraphicsScene")
        self.addStageRect()
        self.addCurrentRect()
        
    def addStageRect(self):
        self.setSceneRect(0, 0, STAGE_X_SIZE / PIXEL_SCALE, STAGE_Y_SIZE / PIXEL_SCALE)
        pen = QtGui.QPen(QtCore.Qt.GlobalColor.white)
        pen.setWidth(0)
        brush = QtGui.QBrush(QtCore.Qt.GlobalColor.black)
        self.stageRect = self.addRect(
            0,
            0,
            STAGE_X_SIZE / PIXEL_SCALE,
            STAGE_Y_SIZE / PIXEL_SCALE,
            pen=pen,
            brush=brush,
        )
        self.stageRect.setZValue(0)
        
    def addCurrentRect(self):
        pen = QtGui.QPen(QtCore.Qt.GlobalColor.green)
        pen.setWidth(0)
        brush_color = QtGui.QColor(0,0,0,0)
        brush = QtGui.QBrush(brush_color)

        #print("Adding rect", 0, 0, WIDTH, HEIGHT)
        self.currentRect = self.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(2)

    def updateCurrentRect(self, x, y):
        self.currentRect.setPos(x / PIXEL_SCALE, y / PIXEL_SCALE)
        # self.centerOn(self.currentRect)
    
    def addImageIfMissing(self, image, pos):
        # if self.acquisition:
        #     print("Not adding image during acquisition")
        #     return
        # if not self.acquisition or len(self.acquisition.grid) == 0:
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
            # print("Adding")
            self.addImage(image, pos)

    def addImage(self, image, pos):
        #print('addImage', draw_data.shape)
        image = image.mirrored(horizontal=True, vertical=False)
        image = image.scaledToHeight(image.height()//10)
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = self.addPixmap(pixmap)
        pm.setPos(pos[0] / PIXEL_SCALE, pos[1] / PIXEL_SCALE)
        pm.setScale(10)
        pm.setZValue(1)
        
    def mouseMoveEvent(self, event):
        pos = event.scenePos()
        message = f"Canvas: {pos.x():.3f}, {pos.y():.3f}, Stage: {pos.x()*PIXEL_SCALE:.3f}, {pos.y()*PIXEL_SCALE:.3f}"
        #print(message)
        self.main_window.statusbar.showMessage(message)
        return super().mouseMoveEvent(event)

    # def mousePressEvent(self, event):
    #     #print("tile scene pressed")
    #     app = QtWidgets.QApplication.instance()
    #     #self.press = QtCore.QPointF(event.pos())

    def mouseReleaseEvent(self, event):
        if (
            abs(
                (
                    event.scenePos()
                    - event.buttonDownScenePos(QtCore.Qt.MouseButton.LeftButton)
                ).manhattanLength()
            )
            == 0.0
        ):
            app = QtWidgets.QApplication.instance()
            if self.main_window.state_value.text() == "Jog":
                print("cancel jog")
                self.main_window.cancel()
            x = event.scenePos().x() - (WIDTH)
            y = event.scenePos().y() - (HEIGHT)
            self.main_window.moveTo(event.scenePos())
        return super().mouseMoveEvent(event)
