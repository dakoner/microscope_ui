import ffmpeg
import os
import numpy as np

import time
from PyQt6 import QtGui, QtWidgets
from PyQt6.uic import loadUi
import serial_interface_qobject

from tile_graphics_view import TileGraphicsView
from zoom_graphics_view import ZoomGraphicsView
from tile_graphics_scene import TileGraphicsScene

# from microscope_esp32_controller_serial import serial_interface_qobject as microscope_serial_qobject
from config import PIXEL_SCALE, CAMERA, XY_FEED

import event_filter


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("microscope_controller.ui", self)

        # self.zoom_view = QtWidgets.QLabel(parent=None)
        # self.zoom_view.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        # self.zoom_view.show()

        # self.image_view.setScaledContents(True)

        # self.toolBar.actionTriggered.connect(self.test)
        # button_action.triggered.connect(self.onMyToolBarButtonClick)

        # self.microscope_esp32_controller_serial =microscope_serial_qobject.SerialInterface('/dev/ttyUSB0')
        # self.microscope_esp32_controller_serial.reset()
        # time.sleep(1)

        # self.microscope_esp32_controller_serial.write("P 2000000 325\n")
        # self.microscope_esp32_controller_serial.write("L1\n")
        # self.microscope_esp32_controller_serial.messageChanged.connect(self.onMessage2Changed)

        if CAMERA == "spin":
            import pyspin_camera_qobject
            self.camera = pyspin_camera_qobject.PySpinCamera()
        # elif CAMERA == "uvclite":
        #     self.camera = uvclite_camera_qobject.UVCLiteCamera()
        elif CAMERA == "quvcobject":
            import quvcobject_camera
            self.camera = quvcobject_camera.QUVCObjectCamera()
        elif CAMERA == "gige":
            import gige_camera_qobject
            self.camera = gige_camera_qobject.GigECamera()
        else:
            print("Unsupported camera type", CAMERA)
            raise
        # self.setContinuous()
        # self.setTrigger()

        self.camera.begin()
        self.camera.camera_play()
        self.state = "None"
        self.m_pos = [-1, -1, -1]

        self.t0 = time.time()

        self.event_filter = event_filter.EventFilter(self)
        self.installEventFilter(self.event_filter)  # keyboard control

        self.camera.imageChanged.connect(self.imageChanged)

        self.serial = serial_interface_qobject.SerialInterface("/dev/ttyUSB0", "dektop")
        self.serial.posChanged.connect(self.onPosChange)
        self.serial.stateChanged.connect(self.onStateChange)
        self.serial.messageChanged.connect(self.onMessageChanged)


        self.scene = TileGraphicsScene(self)
        self.tile_graphics_view = TileGraphicsView(self.scene)
        self.tile_graphics_view.show()
       
       
        # self.zoom_graphics_view = ZoomGraphicsView(self.scene)
        # self.zoom_graphics_view.show()
        
        self.radioButton_23.toggled.connect(self.enableAuto)

        self.prefix = os.path.join("photo", str(time.time()))
        os.makedirs(self.prefix)
        # self.camera.snapshotCompleted.connect(self.snapshotCompleted)

        # self.AeTargetSlider.valueChanged.connect(self.AeTargetChanged)
        # self.AeTargetLabel.setText(str(self.camera.AeTarget))
        # self.AeTargetSlider.setMinimum(self.camera.cap.sExposeDesc.uiTargetMin)
        # self.AeTargetSlider.setMaximum(self.camera.cap.sExposeDesc.uiTargetMax)
        # self.camera.AeTargetChanged.connect(self.AeTargetChangedCallback)

        # self.exposureTimeLabel.setText(str(self.camera.ExposureTime))
        # # needs to be camera-independent
        # #self.exposureTimeSlider.setMinimum(self.camera.cap.sExposeDesc.uiExposeTimeMin)
        # #self.exposureTimeSlider.setMaximum(self.camera.cap.sExposeDesc.uiExposeTimeMax)
        # self.exposureTimeSlider.setMinimum(self.camera._uvc_get_exposure_abs_min())
        # self.exposureTimeSlider.setMaximum(self.camera._uvc_get_exposure_abs_max())
        # self.exposureTimeSlider.setValue(self.camera._uvc_get_exposure_abs_cur())
        # self.exposureTimeSlider.valueChanged.connect(self.ExposureTimeChanged)
        # self.camera.ExposureTimeChanged.connect(self.ExposureTimeChangedCallback)
        
        
        # self.analogGainLabel.setText(str(self.camera.AnalogGain))
        # self.analogGainSlider.setMinimum(self.camera._uvc_get_gain_min())
        # self.analogGainSlider.setMaximum(self.camera._uvc_get_gain_max())
        # self.analogGainSlider.valueChanged.connect(self.AnalogGainChanged)
        # self.camera.AnalogGainChanged.connect(self.AnalogGainChangedCallback)


        self.radioButton_23.toggle()
        #self.enableAuto(False)
        #self.ExposureTimeChangedCallback(25)

        #self.buttonGroup.buttonClicked.connect(self.triggerButtonGroupClicked)
        # self.swToggleRadioButton.toggled.connect(self.enableSoftwareTrigger)
        # self.swTogglePushButton.pressed.connect(self.softwareTrigger)
        # self.hwToggleRadioButton.toggled.connect(self.enableHardwareTrigger)
        

        self.serial.write("$Report/Interval=1\n")
        self.serial.write("?")

    def imageChanged(self, image):
        #self.movie.write(img.astype(np.uint8).tobytes())
        #self.process.stdin.write(img.astype(np.uint8).tobytes())

        if self.state == "Jog" or self.state == "Run":
            self.scene.addImageIfMissing(image, self.m_pos)
            # return

        # s = img.shape
        # if s[2] == 1:
        #     format = QtGui.QImage.Format.Format_Grayscale8
        # elif s[2] == 3:
        #     format = QtGui.QImage.Format.Format_RGB888
        # image = QtGui.QImage(img, s[1], s[0], format)
        # image = image.mirrored(horizontal=False, vertical=False)
        self.curr_image = image
        # w = self.image_view.mapFromGlobal(QtGui.QCursor.pos())
        # r = QtCore.QRect(w.x(), w.y() , 256, 256)
        # zoom_image = image.copy(r)
        # zoom_image = zoom_image.scaledToWidth(1024)
        # self.zoom_view.setFixedSize(1024, 1024)
        # self.zoom_view.setPixmap(QtGui.QPixmap.fromImage(zoom_image))
        # self.image_view.setFixedSize(s[1], s[0])
        pixmap = QtGui.QPixmap.fromImage(image)
        # pixmap = pixmap.scaled(
        #     self.image_view.size(),
        #     QtCore.Qt.KeepAspectRatio,
        #     QtCore.Qt.SmoothTransformation,
        # )
        self.image_view.setPixmap(pixmap)

    def onMessageChanged(self, message):
        self.textEdit.append(message)

    def onPosChange(self, x, y, z, t):
        self.m_pos = [x, y, z]
        self.x_value.display(x)
        self.y_value.display(y)
        self.z_value.display(z)
        self.scene.updateCurrentRect(x, y)

    def onStateChange(self, state):
        self.state = state
        self.state_value.setText(state)


    def reset(self):
        self.serial.reset()

    def unlock(self):
        self.serial.write("$X\n")

    def home(self):
        self.serial.write("$H\n")

    def cancel(self):
        self.serial.cancel()
        # self.client.publish(f"{TARGET}/cancel", "")

    def moveTo(self, position):
        x = position.x() * PIXEL_SCALE
        y = position.y() * PIXEL_SCALE
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}\n"
        self.serial.write(cmd)
        
    def snapshotCompleted(self, frame):
        format = QtGui.QImage.Format_RGB888
        s = frame.shape
        image = QtGui.QImage(frame, s[1], s[0], format)
        t = str(time.time())
        filename = f"{self.prefix}/test.{t}.png"
        image.save(filename)


    def AnalogGainChanged(self, analog_gain):
        print("AnalogGainChanged", analog_gain)
        self.camera.AnalogGain = analog_gain

    def AnalogGainChangedCallback(self, analog_gain):
        print("AnalogGainChangedCallback", analog_gain)
        self.analogGainSlider.setValue(int(analog_gain))
        self.analogGainLabel.setText(str(int(analog_gain)))

    def enableAuto(self, value):
        print("enableAuto", value)
        self.groupBox_6.setEnabled(value)
        self.groupBox_5.setEnabled(not value)
        # self.camera.AeState = value

    def AeTargetChanged(self, target):
        print("AeTargetChanged", target)
        self.camera.AeTarget = target

    def AeTargetChangedCallback(self, value):
        print("AeTargetChangedCallback", value)
        self.AeTargetSlider.setValue(int(value))
        self.AeTargetLabel.setText(str(int(value)))

    def ExposureTimeChanged(self, exposure):
        self.camera.ExposureTime = exposure

    def ExposureTimeChangedCallback(self, exposure):
        self.camera.ExposureTime = exposure
        self.exposureTimeSlider.setValue(int(exposure))
        self.exposureTimeLabel.setText(str(int(exposure)))

    def onMessage2Changed(self, *args):
        print("message2 changed", args)

    # def setContinuous(self):
    #     self.camera.AcquisitionMode = 'Continuous'
    #     self.camera.ExposureAuto = 'Off'
    #     #self.camera.ExposureAuto = 'On'
    #     self.camera.ExposureMode = 'Timed'
    #     self.camera.ExposureTime = 1
    #     #self.camera.AeTarget = 120
    #     #self.camera.AeState = True
    #     #self.camera.TriggerMode = 'Off'
    #     self.camera.StreamBufferHandlingMode = 'NewestOnly'

    # def setTrigger(self):
    #     #self.camera.AcquisitionMode = 'SingleFrame'
    #     self.camera.ExposureAuto = 'Off'
    #     self.camera.ExposureMode = 'Timed'
    #     self.camera.TriggerMode = 'Off'
    #     self.camera.ExposureTime = 251
    #     self.camera.TriggerSource = "Line0"
    #     self.camera.TriggerSelector = 'FrameStart'
    #     self.camera.TriggerActivation = 'RisingEdge'
    #     self.camera.StreamBufferHandlingMode = 'NewestOnly'

    # def trigger(self):
    #     raise RuntimeError
    #     self.camera.stopWorker()
    #     self.setTrigger()
    #     time.sleep(1)
    #     self.microscope_esp32_controller_serial.write("\nX251 0\n")
    #     time.sleep(1)
    #     image_result = self.camera.camera.GetNextImage()
    #     if image_result.IsIncomplete():
    #         print(
    #             "Image incomplete with image status %d ..."
    #             % image_result.GetImageStatus()
    #         )
    #     else:
    #         d = image_result.GetNDArray()
    #         print(d)
    #     time.sleep(1)
    #     # print("setcont")
    #     self.camera.startWorker()
    #     # self.setContinuous()
        

    # def enableSoftwareTrigger(self, value):
    #     print("toggle radio for sw:", value)
    #     self.swTogglePushButton.setEnabled(value)

    # def enableHardwareTrigger(self, value):
    #     print("toggle radio for sw:", value)
    #     self.hwTogglePushButton.setEnabled(value)
    #     # lambda value: self.groupBox_2.setEnabled(value))

    # def softwareTrigger(self, *args):
    #     print("software trigger", args)
    #     print(self.camera.cameraSoftTrigger())

    # def triggerButtonGroupClicked(self, button):
    #     print("trigger button group clicked", button)
    #     if button == self.swToggleRadioButton:
    #         self.camera.TriggerMode = 1
    #     elif button == self.hwToggleRadioButton:
    #         self.camera.TriggerMode = 2
    #     elif button == self.continuousRadioButton:
    #         self.camera.TriggerMode = 0
    #     else:
    #         print("uknown button")
           