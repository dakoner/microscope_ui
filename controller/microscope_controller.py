import time
import functools
import sys
import signal
from video_sender.pyspin_camera import pyspin_camera_qobject
from microscope_esp32_controller_serial import serial_interface_qobject as microscope_serial_qobject
from fluidnc_serial import serial_interface_qobject

from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
sys.path.append("..")
from microscope_ui.config import PIXEL_SCALE, MQTT_HOST, TARGET, XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE, HEIGHT, WIDTH, FOV_X, FOV_Y
from mqtt_qobject import MqttClient



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("controller/microscope_controller.ui", self)
        

        #self.toolBar.actionTriggered.connect(self.test)
        #button_action.triggered.connect(self.onMyToolBarButtonClick)

        self.client = MqttClient(self)
        self.client.hostname = MQTT_HOST
        self.client.connectToHost()

        self.serial = serial_interface_qobject.SerialInterface('/dev/ttyUSB0', "dektop")
        self.serial.posChanged.connect(self.onPosChange)
        self.serial.stateChanged.connect(self.onStateChange)
        self.serial.messageChanged.connect(self.onMessageChanged)


        self.microscope_esp32_controller_serial =microscope_serial_qobject.SerialInterface('/dev/ttyUSB1')
        self.microscope_esp32_controller_serial.write("P2000000 6\n")
        self.serial.messageChanged.connect(self.onMessage2Changed)

        self.camera = pyspin_camera_qobject.PySpinCamera()
        self.camera.imageChanged.connect(self.imageChanged)
        self.setContinuous()

        self.camera.startWorker()
        self.camera.begin()

        self.state = 'None'
        self.m_pos = [-1, -1, -1]

        self.t0 = time.time()
    def onMessage2Changed(self, *args):
        print('message2 changed', args)

    def setContinuous(self):
        self.camera.AcquisitionMode = 'Continuous'
        self.camera.ExposureAuto = 'Off'
        self.camera.ExposureMode = 'Timed'
        self.camera.ExposureTime = 251
        self.camera.TriggerMode = 'Off'
        self.camera.StreamBufferHandlingMode = 'NewestOnly'

    def setTrigger(self):
        #self.camera.AcquisitionMode = 'SingleFrame'
        self.camera.ExposureAuto = 'Off'
        self.camera.ExposureMode = 'TriggerWidth'
        #self.camera.TriggerMode = 'On'
        self.camera.TriggerSource = "Line3"
        self.camera.TriggerSelector = 'FrameStart'
        self.camera.TriggerActivation = 'RisingEdge'
        self.camera.StreamBufferHandlingMode = 'NewestOnly'

    def imageChanged(self, draw_data):
        t0 = time.time()
        self.t0 = t0
        if self.state == 'Jog' or self.state == 'Run':
            f = draw_data.flatten()
            val = f.sum()/len(f)
            if self.tile_graphics_view.acquisition is None:
                self.tile_graphics_view.addImageIfMissing(draw_data, self.m_pos)
            
        if self.state != 'Home':
            s = draw_data.shape
            if s[2] == 1:
                format = QtGui.QImage.Format_Grayscale8
            elif s[2] == 3:
                format = QtGui.QImage.Format_RGB888

            image = QtGui.QImage(draw_data, s[1], s[0], format)
            pixmap = QtGui.QPixmap.fromImage(image)
            #self.image_view.setFixedSize(s[0], s[1])
            self.image_view.setPixmap(pixmap)

    def onMessageChanged(self, message):
        pass
        #print("message:", message)

    def onPosChange(self, x, y, z, t):
        self.m_pos = [x,y,z]
        self.x_value.display(x)
        self.y_value.display(y)
        self.z_value.display(z)
        self.tile_graphics_view.updateCurrentRect(x, y)

    def onStateChange(self, state):
        self.state = state
        self.state_value.setText(state)

    def trigger(self):
        self.camera.stopWorker()
        self.setTrigger()
        time.sleep(1)
        self.microscope_esp32_controller_serial.write("\nX251 0\n")
        time.sleep(1)
        image_result = self.camera.camera.GetNextImage()
        if image_result.IsIncomplete():
            print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
        else:
            d = image_result.GetNDArray()
            print(d)
        time.sleep(1)
        # print("setcont")
        self.camera.startWorker()
        self.setContinuous()
        

    def reset(self):
        self.serial.reset()

    def unlock(self):
        self.serial.write("$X\n")

    def home(self):
        self.serial.write("$H\n")

    def cancel(self):
        self.serial.cancel()
        #self.client.publish(f"{TARGET}/cancel", "")

    def moveTo(self, position):
        print("move to", position)
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        print("move to stage coord", x, y)
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}\n"
        self.serial.write(cmd)

class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = MainWindow()
        self.main_window.show()#showMaximized()

    #     self.installEventFilter(self)

    # def eventFilter(self, widget, event):
    #     if event.type() not in (QtCore.QEvent.WindowDeactivate, QtCore.QEvent.Paint, QtCore.QEvent.UpdateRequest, QtCore.QEvent.MetaCall, QtCore.QEvent.ActivationChange, QtCore.QEvent.HoverMove, QtCore.QEvent.HoverLeave, QtCore.QEvent.HoverEnter, QtCore.QEvent.ApplicationDeactivate, QtCore.QEvent.ApplicationStateChange, QtCore.QEvent.ToolTip, QtCore.QEvent.Leave,  QtCore.QEvent.FocusAboutToChange, QtCore.QEvent.CursorChange, QtCore.QEvent.ChildRemoved, QtCore.QEvent.DeferredDelete):
    #         print(widget.objectName(), event.type())
    #     return False


    def test(self, action):
        print("action", action.objectName())
        if action.objectName() == 'stopAction':
            print("STOP")
            self.cancel()
            self.main_window.tile_graphics_view.stopAcquisition()



if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()
