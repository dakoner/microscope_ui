import time
import functools
import sys
import signal
from video_sender.pyspin_camera import pyspin_camera_qobject
from fluidnc_serial import serial_interface_qobject

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
sys.path.append("..")
from microscope_ui.config import PIXEL_SCALE, MQTT_HOST, TARGET, XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE, HEIGHT, WIDTH, FOV_X, FOV_Y
from mqtt_qobject import MqttClient

class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = QtWidgets.QMainWindow()
        loadUi("controller/microscope_controller.ui", self.main_window)
        self.main_window.dumpObjectTree()
        self.main_window.setFocusPolicy(True)
        self.main_window.show()

        self.installEventFilter(self)

        self.main_window.toolBar.actionTriggered.connect(self.test)
    
        #button_action.triggered.connect(self.onMyToolBarButtonClick)

        self.client = MqttClient(self)
        self.client.hostname = MQTT_HOST
        self.client.connectToHost()

        self.serial = serial_interface_qobject.SerialInterface('/dev/ttyUSB0', "dektop")
        self.serial.posChanged.connect(self.onPosChange)
        self.serial.stateChanged.connect(self.onStateChange)
        self.serial.messageChanged.connect(self.onMessageChanged)

        self.p = pyspin_camera_qobject.PySpinCamera()
        self.p.imageChanged.connect(self.imageChanged)
        self.p.begin()


        self.state = 'None'
        self.m_pos = [-1, -1, -1]

        self.t0 = time.time()

    def onMessageChanged(self, message):
        print("message:", message)

    def onPosChange(self, x, y, z):
        self.m_pos = [x,y,z]
        self.main_window.x_value.display(x)
        self.main_window.y_value.display(y)
        self.main_window.z_value.display(z)
        self.main_window.tile_graphics_view.updateCurrentRect(x, y)

    def onStateChange(self, state):
        self.state = state
        self.main_window.state_value.setText(state)

    def eventFilter(self, widget, event):
        if isinstance(event, QtGui.QKeyEvent):
            return self.handleKeyEvent(widget, event)
        elif isinstance(event, QtGui.QMouseEvent):
            return self.handleMouseEvent(widget, event)
        return False

    def handleKeyEvent(self, widget, event):
        key = event.key()
        type_ = event.type()
        if type_ == QtCore.QEvent.KeyPress:
            if key == QtCore.Qt.Key_Plus:
                self.main_window.tile_graphics_view.scale(1.1, 1.1)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_Minus:
                self.main_window.tile_graphics_view.scale(0.9, 0.9)    
                event.accept()
                return True
            elif key == QtCore.Qt.Key_C:
                self.cancel()
                #self.client.publish(f"{TARGET}/cancel", "")
                event.accept()
                return True
            elif key == QtCore.Qt.Key_H:
                self.cancel()
                self.home()
                #self.client.publish(f"{TARGET}/command", "$H")
                event.accept()
                return True
            elif key == QtCore.Qt.Key_S:
                #self.client.publish(f"{TARGET}/cancel", "")
                self.cancel()
                self.main_window.tile_graphics_view.stopAcquisition()
                event.accept()
                return True
            elif key == QtCore.Qt.Key_P:
                draw_data = self.camera.image
                pos = self.pos
                fname = f"image_{int(time.time())}.tif"
                image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
                image.save(fname)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_R:
                self.scene.clear()
                self.main_window.tile_graphics_view.addStageRect()
                self.main_window.tile_graphics_view.addCurrentRect()

            elif key == QtCore.Qt.Key_Left:
                if self.state == "Idle":
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}\n"
                    self.serial.write(cmd)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_Right:
                if self.state == "Idle":
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}\n"
                    self.serial.write(cmd)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_Up:
                if self.state == "Idle":
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}\n"
                    self.serial.write(cmd)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_Down:
                if self.state == "Idle":
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}\n"
                    self.serial.write(cmd)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_PageUp:
                if self.state == "Idle":
                    cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                    self.serial.write(cmd)
                event.accept()
                return True
            elif key == QtCore.Qt.Key_PageDown:
                if self.state == "Idle":
                    cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                    self.serial.write(cmd)
                event.accept()
                return True
        
        return super().eventFilter(widget, event)

    def handleMouseEvent(self, widget, event):
        print("handleMouseEvent", widget, event)
        print(widget.objectName())
        if widget.parent() == self.main_window.tile_graphics_view:
            pt = self.main_window.tile_graphics_view.mapToScene(event.x(), event.y())
            self.main_window.statusbar.showMessage(f"Canvas: {pt.x():.3f}, {pt.y():.3f}, Stage: {pt.x()*PIXEL_SCALE:.3f}, {pt.y()*PIXEL_SCALE:.3f}")
            if event.type() == QtCore.QEvent.MouseButtonPress:
                self.press = self.main_window.tile_graphics_view.mapToScene(event.pos())
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                sp = self.main_window.tile_graphics_view.mapToScene(event.pos())
                if (self.press - sp).manhattanLength() == 0.0:
                    if app.main_window.state_value.text() == 'Jog':
                        app.cancel()
                    self.moveTo(self.press)
        if widget == self.main_window.tile_graphics_view.scene:
            print("scene event")
        return False

    def test(self, action):
        print("action", action.objectName())
        if action.objectName() == 'stopAction':
            print("STOP")
            self.cancel()
            self.main_window.tile_graphics_view.stopAcquisition()



    def home(self):
        self.serial.write("$H\n")

    def cancel(self):
        pass
        #self.client.publish(f"{TARGET}/cancel", "")
        


    def imageChanged(self, draw_data):
        t0 = time.time()
        self.t0 = t0
        if self.state == 'Jog' or self.state == 'Run':
            f = draw_data.flatten()
            val = f.sum()/len(f)
            if val > 10:
                self.main_window.tile_graphics_view.addImageIfMissing(draw_data, self.m_pos)
            
        if self.state != 'Home':
            s = draw_data.shape
            if s[2] == 1:
                format = QtGui.QImage.Format_Grayscale8
            elif s[2] == 3:
                format = QtGui.QImage.Format_RGB888

            image = QtGui.QImage(draw_data, s[1], s[0], format)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.main_window.image_view.setPixmap(pixmap)


    def moveTo(self, position):
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}"
        self.serial.write(cmd)
        #self.client.publish(f"{TARGET}/command", cmd)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()
