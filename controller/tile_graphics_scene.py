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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        if not self.currentRect:
            self.addCurrentRect()
        self.currentRect.setPos(x / PIXEL_SCALE, y / PIXEL_SCALE)
        # self.centerOn(self.currentRect)
    
    def addImageIfMissing(self, draw_data, pos):
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
            self.addImage(draw_data, pos)

    def addImage(self, draw_data, pos):
        #print('addImage', draw_data.shape)
        image = QtGui.QImage(
            draw_data,
            draw_data.shape[1],
            draw_data.shape[0],
            QtGui.QImage.Format.Format_RGB888,
        )
        image = image.mirrored(horizontal=True, vertical=False)
        image = image.scaledToHeight(72)
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = self.addPixmap(pixmap)
        pm.setPos(pos[0] / PIXEL_SCALE, pos[1] / PIXEL_SCALE)
        pm.setScale(10)
        pm.setZValue(1)
        
    def mouseMoveEvent(self, event):
        app = QtWidgets.QApplication.instance()
        pos = event.scenePos()
        message = f"Canvas: {pos.x():.3f}, {pos.y():.3f}, Stage: {pos.x()*PIXEL_SCALE:.3f}, {pos.y()*PIXEL_SCALE:.3f}"
        #print(message)
        app.main_window.statusbar.showMessage(message)
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
            if app.main_window.state_value.text() == "Jog":
                print("cancel jog")
                app.main_window.cancel()
            x = event.scenePos().x() - (WIDTH)
            y = event.scenePos().y() - (HEIGHT)
            app.main_window.moveTo(event.scenePos())
        return super().mouseMoveEvent(event)
