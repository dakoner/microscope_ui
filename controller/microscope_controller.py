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



class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, width, height, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, width, height)
        self.setSceneRect(0, 0, width, height)
        self.showMaximized()
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)


    def resizeEvent(self, event):
        # fitInView interferes with scale()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        print("ScannedImage event")
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_Plus:
            self.scale(2,2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.5,0.5)

    def addImage(self, pos, image):
        a = QtGui.QImage(image.width(), image.height(),
                QtGui.QImage.Format_ARGB32)
        a.fill(QtGui.QColor(255, 255, 255, 255))
        r = self.scene.addRect(pos.x(), pos.y(), image.width(), image.height())
        qp = QtGui.QPainterPath()
        qp.addRect(r.sceneBoundingRect())
        for item in r.collidingItems():
            qp2 = QtGui.QPainterPath()
            if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                qp2.addRect(item.sceneBoundingRect())
                qp3 = qp.intersected(qp2)
                qp3.closeSubpath()
                x = qp3.boundingRect().x()-pos.x()
                y = qp3.boundingRect().y()-pos.y()
                width = qp3.boundingRect().width()
                height = qp3.boundingRect().height()
                if width < height:
                    linearGrad = QtGui.QLinearGradient(0, 0, width, 1)
                else:
                    linearGrad = QtGui.QLinearGradient(0, 0, 1, height)

                linearGrad.setColorAt(0, QtGui.QColor(0, 0, 0, 255))
                linearGrad.setColorAt(1, QtGui.QColor(255, 255, 255, 255))
                p = QtGui.QPainter()
                p.begin(a)
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QBrush(linearGrad))
                p.drawRect(x, y, width, height)
                p.end()
                
        #z = QtWidgets.QLabel()
        #z.setPixmap(QtGui.QPixmap.fromImage(a))
        # self.tw.addTab(z, "image")
        # self.tw.showMaximized()
        #z.show()
        image.setAlphaChannel(a)
        pixmap = QtGui.QPixmap.fromImage(image)

        self.scene.removeItem(r)

        pm = self.scene.addPixmap(pixmap)
        
        pm.setPos(pos)
        pm.setZValue(2)

    def save(self, fname):
        r = self.scene.sceneRect()
        image = QtGui.QImage(r.width(), r.height(), QtGui.QImage.Format_ARGB32)
        p = QtGui.QPainter(image)
        self.scene.render(p)
        p.end()
        image.save(fname)
        print("Save done", fname)
 
class ImageView(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(True)        

    def keyPressEvent(self, event):
        print("ImageView keypressevent",event)
 
        app = QtWidgets.QApplication.instance()
        self.client = app.client
        self.camera = app.camera
        self.scene = app.main_window.tile_graphics_view.scene
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
            app.main_window.tile_graphics_view.stopAcquisition()
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

       
class Acquisition():
    def __init__(self, lastRubberBand):
        self.lastRubberBand = lastRubberBand
        self.grid = []
        self.counter = 0
        self.scanned_image_tabwidget =  QtWidgets.QTabWidget()

    def startAcquisition(self):
        self.orig_grid = self.generateGrid(*self.lastRubberBand)
        
        self.startPos = QtCore.QPointF(self.lastRubberBand[0].x(), self.lastRubberBand[0].y())
        width = int(self.lastRubberBand[1].x()-self.lastRubberBand[0].x())+WIDTH
        height = int(self.lastRubberBand[1].y()-self.lastRubberBand[0].y())+HEIGHT
        scanned_image = ScannedImage(width, height)
        self.scanned_image_tabwidget.addTab(scanned_image, str(self.counter))
        self.scanned_image_tabwidget.show()

        app=QtWidgets.QApplication.instance()
        self.grid = self.orig_grid[:]
        addr, cmd = self.grid.pop(0)
        app.client.publish(f"{TARGET}/command", cmd)


    def snapPhoto(self):
        app=QtWidgets.QApplication.instance()
        camera = app.camera
        draw_data = camera.image
        pos = camera.pos
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = app.main_window.tile_graphics_view.scene.addPixmap(pixmap)
        pm.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        pm.setZValue(1)
        app.main_window.image_view.setPixmap(pixmap)

        current_pos = QtCore.QPointF(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
        self.scanned_image_tabwidget.widget(self.counter).addImage(current_pos-self.startPos, image)

    def doAcquisition(self):
        if len(self.grid):
            if self.grid == [None]:
                self.snapPhoto()
                self.scanned_image_tabwidget.widget(self.counter).save(f"c:\\Users\\dek\\Desktop\\acquisition\\frame.{self.counter}.tif")
                self.counter += 1
                self.startAcquisition()
            else:
                self.snapPhoto()
                addr, cmd = self.grid.pop(0)
                app=QtWidgets.QApplication.instance()
                app.client.publish(f"{TARGET}/command", cmd)

    def generateGrid(self, from_, to):
        grid = []
        dz = [0]

        x_min = from_.x()* PIXEL_SCALE
        y_min =  from_.y()* PIXEL_SCALE
        x_max = to.x()* PIXEL_SCALE
        y_max =  to.y()* PIXEL_SCALE

        app=QtWidgets.QApplication.instance()

        z = app.camera.pos[2]
        num_z = len(dz)
        ys = np.arange(y_min, y_max, FOV_Y)
        #ys = [y_min, y_max]
        num_y = len(ys)
        xs = np.arange(x_min, x_max, FOV_X)
        #xs = [x_min, x_max]
        num_x = len(xs)
        
        for i, deltaz in enumerate(dz):           
            for j, gy in enumerate(ys):
                # if j % 2 == 0:
                #     xs_ = xs
                # else:
                #     xs_ = xs[::-1]
                # print(xs_)
                ##Disable bidirectional scanning since it interferes with tile blending
                xs_ = xs
                for k, gx in enumerate(xs_):
                    curr_z = z + deltaz
                    g = f"$J=G90 G21 F{XY_FEED:.3f} X{gx:.3f} Y{gy:.3f} Z{curr_z:.3f}"
                    grid.append(((i,j,k),g))

        grid.append(None)
        return grid


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
       

    
class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = QtWidgets.QMainWindow()
        loadUi("controller/microscope_controller.ui", self.main_window)

        self.main_window.showMaximized()

        self.installEventFilter(self)

        self.main_window.toolBar.actionTriggered.connect(self.test)
    
        #button_action.triggered.connect(self.onMyToolBarButtonClick)

        self.client = MqttClient(self)
        self.client.hostname = "raspberrypi.local"
        self.client.connectToHost()

        self.camera = ImageZMQCameraReader()
        self.camera.imageChanged.connect(self.imageChanged)
        self.camera.stateChanged.connect(self.stateChanged)
        self.camera.posChanged.connect(self.posChanged)
        self.camera.start()

    def eventFilter(self, widget, event):
        if widget == self.main_window.image_view and isinstance(event, QtGui.QKeyEvent):
            print("key press for image view")
            self.main_window.image_view.keyPressEvent(event)
        elif widget == self.main_window.tile_graphics_view and isinstance(event, QtGui.QKeyEvent):
            print("key press for tile graphics view")
            self.main_window.image_view.keyPressEvent(event)
        return False

    def test(self, action):
        print("action", action.objectName())
        if action.objectName() == 'stopAction':
            print("STOP")
            self.cancel()
            self.main_window.tile_graphics_view.stopAcquisition()



    def cancel(self):
        self.client.publish(f"{TARGET}/cancel", "")
        

    def stateChanged(self, state):
        self.main_window.state_value.setText(state)
        if state == 'Idle':
            self.main_window.tile_graphics_view.doAcquisition()
            

    def posChanged(self, pos):
        self.main_window.x_value.display(pos[0])
        self.main_window.y_value.display(pos[1])
        self.main_window.z_value.display(pos[2])
        self.main_window.tile_graphics_view.currentRect.setPos(pos[0]/PIXEL_SCALE, pos[1]/PIXEL_SCALE)
       

    def imageChanged(self, draw_data):
        state = self.camera.state
        pos = self.camera.pos
        if state == 'Jog':
            self.main_window.tile_graphics_view.addImageIfMissing(draw_data, pos)
            
        if state != 'Home':
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.main_window.image_view.setPixmap(pixmap)


    def moveTo(self, position):
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}"
        self.client.publish(f"{TARGET}/command", cmd)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()
