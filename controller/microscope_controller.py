import pyqtgraph
import pyqtconsole
import code
import numpy as np
import functools
import json
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
from image_zmq_camera_reader import ImageZMQCameraReader
sys.path.append("..")
from microscope_ui.config import PIXEL_SCALE, TARGET, XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE, HEIGHT, WIDTH, FOV_X, FOV_Y
from mqtt_qobject import MqttClient


def calculate_area(qpolygon):
    area = 0
    for i in range(qpolygon.size()):
        p1 = qpolygon[i]
        p2 = qpolygon[(i + 1) % qpolygon.size()]
        d = p1.x() * p2.y() - p2.x() * p1.y()
        area += d
    return abs(area) / 2

class PythonConsole(QtWidgets.QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.appendPlainText('>>> ')
        #self.installEventFilter(self)
        self.interp = code.InteractiveInterpreter()
        self.curPos = self.textCursor().position()

    # def eventFilter(self, obj, event):
    #     if event.type() == QtCore.QEvent.KeyPress:
    #         if event.key() == QtCore.Qt.Key_Return and self.hasFocus():
    #             c = self.toPlainText()[self.curPos:self.textCursor().position()]
    #             print(c)
    #             result = self.interp.runsource(c)
    #             print(result)
    #             self.appendPlainText("\n>>> ")
    #             self.curPos = self.textCursor().position()

    #     return super().eventFilter(obj, event)

class Scene(QtWidgets.QGraphicsScene):
    def __init__(self, main_window, *args, **kwargs):
        self.main_window = main_window
        super().__init__(*args, **kwargs)

    def mouseMoveEvent(self, event):
        self.main_window.statusbar.showMessage(f"Canvas: {event.scenePos().x():.3f}, {event.scenePos().y():.3f}, Stage: {event.scenePos().x()*PIXEL_SCALE:.3f}, {event.scenePos().y()*PIXEL_SCALE:.3f}")
        return super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self.press = event.scenePos()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (self.press - event.scenePos()).manhattanLength() == 0.0:
            if self.main_window.state_value.text() == 'Jog':
                self.main_window.cancel()
                self.timer = QtCore.QTimer()
                p = functools.partial(self.main_window.moveTo, self.press)
                self.timer.timeout.connect(p)
                self.timer.setSingleShot(True)
                self.timer.start(100)
            else:
                self.main_window.moveTo(self.press)
        return super().mouseReleaseEvent(event)


class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, width, height, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, width, height)
        #self.setSceneRect(0, 0, width, height)
        #self.fitInView(self.scene.sceneRect())
        #self.setFixedSize(width, height)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def resizeEvent(self, event):
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_Plus:
            self.scale(2,2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.5,0.5)

    def addImage(self, pos, image):
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = self.scene.addPixmap(pixmap)
        pm.setPos(pos)
        pm.setZValue(1)

        
class ImageView(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        print("ImageView")
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(True)
        
   

    def keyPressEvent(self, event):
        print("keypress",event)
 
        app = QtWidgets.QApplication.instance()
        self.client = app.main_window.client
        self.camera = app.main_window.camera
        self.scene = app.main_window.scene
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_C:
            print("cancel")
            self.client.publish(f"{TARGET}/cancel", "")
        if key == QtCore.Qt.Key_H:
            print("home")
            self.client.publish(f"{TARGET}/command", "$H")
        elif key == QtCore.Qt.Key_S:
            print("stop")
            self.client.publish(f"{TARGET}/cancel", "")
            self.grid = []
        elif key == QtCore.Qt.Key_R:
            print("reset tiles")
            self.scene.clear()
        elif self.camera.state == "Idle":
            if key == QtCore.Qt.Key_Left:
                print("left")
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Right:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Up:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Down:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Plus:
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Minus:
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
        return super().keyPressEvent(event)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("controller/microscope_controller.ui", self)

        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi.local"
        self.client.connectToHost()

        self.scene = Scene(self)
        
        pen = QtGui.QPen()
        pen.setWidth(1)
        color = QtGui.QColor()
        brush = QtGui.QBrush(color)
        self.stageRect = self.scene.addRect(0, 0, 68/PIXEL_SCALE, 85/PIXEL_SCALE, pen=pen, brush=brush)
        self.stageRect.setZValue(0)

        pen = QtGui.QPen(QtCore.Qt.green)
        pen.setWidth(50)
        brush = QtGui.QBrush()
        self.currentRect = self.scene.addRect(0, 0, WIDTH, HEIGHT, pen=pen, brush=brush)
        self.currentRect.setZValue(1)

        self.scene.setSceneRect(self.stageRect.boundingRect())
        self.graphicsView.setScene(self.scene)
        #self.graphicsView.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        self.graphicsView.setMouseTracking(True)
        self.graphicsView.update()

        self.graphicsView.rubberBandChanged.connect(self.rubberBandChanged)



        self.camera = ImageZMQCameraReader()
        self.camera.imageChanged.connect(self.imageChanged)
        self.camera.stateChanged.connect(self.stateChanged)
        self.camera.posChanged.connect(self.posChanged)
        self.camera.start()

        self.grid = []

    def rubberBandChanged(self, rect, from_ , to):
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
            rect.setZValue(1)

            self.grid = self.generateGrid(*self.lastRubberBand)
            self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
            
            self.scanned_image = ScannedImage(
                int(self.lastRubberBand[1].x()-self.lastRubberBand[0].x())+WIDTH, 
                int(self.lastRubberBand[1].y()-self.lastRubberBand[0].y())+HEIGHT)
            self.scanned_image.show()


            addr, cmd = self.grid.pop(0)
            self.client.publish(f"{TARGET}/command", cmd)
        else:
            self.lastRubberBand = from_, to


    def generateGrid(self, from_, to):
        grid = []
        dz = [0]

        x_min = from_.x()* PIXEL_SCALE
        y_min =  from_.y()* PIXEL_SCALE
        x_max = to.x()* PIXEL_SCALE
        y_max =  to.y()* PIXEL_SCALE

        z = self.camera.pos[2]
        num_z = len(dz)
        ys = np.arange(y_min, y_max, FOV_Y)
        num_y = len(ys)
        xs = np.arange(x_min, x_max, FOV_X)
        num_x = len(xs)
        
        for i, deltaz in enumerate(dz):           
            for j, gy in enumerate(ys):
                if j % 2 == 0:
                    xs_ = xs
                else:
                    xs_ = xs[::-1]
                for k, gx in enumerate(xs_):
                    curr_z = z + deltaz
                    g = f"$J=G90 G21 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f} Z{curr_z:.3f}"
                    grid.append(((i,j,k),g))

        grid.append(None)
        return grid

    def resizeEvent(self, *args):
        print("resize event", args)
        self.graphicsView.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def cancel(self):
        self.client.publish(f"{TARGET}/cancel", "")
        
    def snapPhoto(self):
        draw_data = self.camera.image
        pos = self.camera.pos
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = self.scene.addPixmap(pixmap)
        pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        pm.setZValue(1)
        self.image_view.setPixmap(pixmap)

        a = QtGui.QImage(
                np.full((draw_data.shape[1], draw_data.shape[0]), 127, dtype=np.ubyte),
                draw_data.shape[1], draw_data.shape[0],
                QtGui.QImage.Format_Alpha8)
        image.setAlphaChannel(a)
        current_pos = QtCore.QPointF(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        self.scanned_image.addImage(current_pos-self.startPos, image)

    def stateChanged(self, state):
        self.state_value.setText(state)
        if state == 'Idle':
            if len(self.grid):
                if self.grid == [None]:
                    self.snapPhoto()
                    self.grid = []
                else:
                    addr, cmd = self.grid.pop(0)
                    self.client.publish(f"{TARGET}/command", cmd)
                    self.snapPhoto()

    def posChanged(self, pos):
        self.x_value.display(pos[0])
        self.y_value.display(pos[1])
        self.z_value.display(pos[2])
        self.currentRect.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
       

    def imageChanged(self, draw_data):
        state = self.camera.state
        pos = self.camera.pos
        if state == 'Jog' and len(self.grid) == 0:
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
        if state != 'Home':
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.image_view.setPixmap(pixmap)


    def moveTo(self, position):
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}"
        self.client.publish(f"{TARGET}/command", cmd)
    
class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = MainWindow()
        self.main_window.showMaximized()

        self.installEventFilter(self)

    def eventFilter(self, widget, event):
        if widget == self.main_window.image_view and isinstance(event, QtGui.QKeyEvent):
            print("key press for image view")
            self.main_window.image_view.keyPressEvent(event)
        return False

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()
