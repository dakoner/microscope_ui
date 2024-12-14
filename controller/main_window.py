import ffmpeg
import os
import numpy as np

import time
from PyQt6 import QtGui, QtCore, QtWidgets
from PyQt6.uic import loadUi
import serial_interface_qobject

import gige_camera_qobject
import uvc_camera_qobject
import uvclite_camera_qobject
from tile_graphics_view import TileGraphicsView

# from microscope_esp32_controller_serial import serial_interface_qobject as microscope_serial_qobject
from config import PIXEL_SCALE, CAMERA, XY_FEED
import event_filter
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        elif CAMERA == "uvc":
            self.camera = uvc_camera_qobject.UVCCamera(3)
        elif CAMERA == "uvclite":
            self.camera = uvclite_camera_qobject.UVCLiteCamera()
        elif CAMERA == "gige":
            self.camera = gige_camera_qobject.GigECamera()
        else:
            print("Unsupported camera type", CAMERA)
            raise
        # self.setContinuous()
        # self.setTrigger()

        # self.camera.startWorker()
        self.camera.begin()
        self.camera.camera_play()


        # self.process = (
        #     ffmpeg.input(
        #         "pipe:",
        #         format="rawvideo",
        #         pix_fmt="rgb24",
        #         s="{}x{}".format(1280, 1024),
        #     ).filter('scale', 640, -1)
        #     .output(
        #         "movie.mp4", pix_fmt="yuv420p", vcodec="libx264", preset="ultrafast", crf=27)
        #     .overwrite_output()
        #     .run_async(pipe_stdin=True)
        # )
        #self.movie = open("movie.raw", "wb")
        self.state = "None"
        self.m_pos = [-1, -1, -1]

        self.t0 = time.time()

        self.event_filter = event_filter.EventFilter(self)
        self.installEventFilter(self.event_filter)  # keyboard control

        loadUi("microscope_controller.ui", self)
        self.camera.imageChanged.connect(self.imageChanged)

        self.serial = serial_interface_qobject.SerialInterface("/dev/ttyUSB1", "dektop")
        self.serial.posChanged.connect(self.onPosChange)
        self.serial.stateChanged.connect(self.onStateChange)
        self.serial.messageChanged.connect(self.onMessageChanged)

        self.tile_graphics_view = TileGraphicsView()
        self.tile_graphics_view.show()
        self.buttonGroup.buttonClicked.connect(self.triggerButtonGroupClicked)
        self.swToggleRadioButton.toggled.connect(self.enableSoftwareTrigger)
        self.swTogglePushButton.pressed.connect(self.softwareTrigger)
        self.hwToggleRadioButton.toggled.connect(self.enableHardwareTrigger)
        self.radioButton_23.toggled.connect(self.enableAuto)

        self.prefix = os.path.join("photo", str(time.time()))
        os.makedirs(self.prefix)
        # self.camera.snapshotCompleted.connect(self.snapshotCompleted)

        self.AeTargetSlider.valueChanged.connect(self.AeTargetChanged)
        # self.AeTargetLabel.setText(str(self.camera.AeTarget))
        # self.AeTargetSlider.setMinimum(self.camera.cap.sExposeDesc.uiTargetMin)
        # self.AeTargetSlider.setMaximum(self.camera.cap.sExposeDesc.uiTargetMax)
        # self.camera.AeTargetChanged.connect(self.AeTargetChangedCallback)

        self.exposureTimeSlider.valueChanged.connect(self.ExposureTimeChanged)
        self.exposureTimeLabel.setText(str(self.camera.ExposureTime))
        # needs to be camera-independent
        #self.exposureTimeSlider.setMinimum(self.camera.cap.sExposeDesc.uiExposeTimeMin)
        #self.exposureTimeSlider.setMaximum(self.camera.cap.sExposeDesc.uiExposeTimeMax)
        self.exposureTimeSlider.setMinimum(self.camera._uvc_get_exposure_abs_min())
        self.exposureTimeSlider.setMaximum(self.camera._uvc_get_exposure_abs_max())
        self.exposureTimeSlider.setValue(self.camera._uvc_get_exposure_abs_cur())
        self.camera.ExposureTimeChanged.connect(self.ExposureTimeChangedCallback)
        self.radioButton_23.toggle()
        
        self.enableAuto(True)
        self.ExposureTimeChanged(650)

        # self.analogGainSlider.valueChanged.connect(self.AnalogGainChanged)
        # self.analogGainLabel.setText(str(self.camera.AnalogGain))
        # self.analogGainSlider.setMinimum(self.camera.cap.sExposeDesc.uiAnalogGainMin)
        # self.analogGainSlider.setMaximum(self.camera.cap.sExposeDesc.uiAnalogGainMax)
        # self.camera.AnalogGainChanged.connect(self.AnalogGainChangedCallback)

    def snapshotCompleted(self, frame):
        format = QtGui.QImage.Format_RGB888
        s = frame.shape
        image = QtGui.QImage(frame, s[1], s[0], format)
        t = str(time.time())
        filename = f"{self.prefix}/test.{t}.png"
        image.save(filename)

    def enableSoftwareTrigger(self, value):
        print("toggle radio for sw:", value)
        self.swTogglePushButton.setEnabled(value)

    def enableHardwareTrigger(self, value):
        print("toggle radio for sw:", value)
        self.hwTogglePushButton.setEnabled(value)
        # lambda value: self.groupBox_2.setEnabled(value))

    def softwareTrigger(self, *args):
        print("software trigger", args)
        print(self.camera.cameraSoftTrigger())

    def triggerButtonGroupClicked(self, button):
        print("trigger button group clicked", button)
        if button == self.swToggleRadioButton:
            self.camera.TriggerMode = 1
        elif button == self.hwToggleRadioButton:
            self.camera.TriggerMode = 2
        elif button == self.continuousRadioButton:
            self.camera.TriggerMode = 0
        else:
            print("uknown button")

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
        self.camera.AeState = not value

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

    def imageChanged(self, img):
        t0 = time.time()
        #self.movie.write(img.astype(np.uint8).tobytes())
        #self.process.stdin.write(img.astype(np.uint8).tobytes())

        self.t0 = t0
        if self.state == "Jog" or self.state == "Run":
            self.tile_graphics_view.addImageIfMissing(img, self.m_pos)
            # return

        # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # img = cv2.normalize(img, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
        # img = (255*img).astype(np.uint8)

        # ima        image = QtGui.QImage(draw_data, s[1], s[0], format)
        # image = image.mirrored(horizontal=True, vertical=False)
        # pixmap = QtGui.QPixmap.fromImage(image)
        # self.image_view.setFixedSize(1440//2, 1080//2)
        # #self.image_view.setFixedSize(s[1], s[0])
        # self.image_view.setPixmap(pixmap)

        s = img.shape
        if s[2] == 1:
            format = QtGui.QImage.Format.Format_Grayscale8
        elif s[2] == 3:
            format = QtGui.QImage.Format.Format_RGB888
        image = QtGui.QImage(img, s[1], s[0], format)
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
        self.tile_graphics_view.updateCurrentRect(x, y)

    def onStateChange(self, state):
        self.state = state
        self.state_value.setText(state)

    def trigger(self):
        raise RuntimeError
        self.camera.stopWorker()
        self.setTrigger()
        time.sleep(1)
        self.microscope_esp32_controller_serial.write("\nX251 0\n")
        time.sleep(1)
        image_result = self.camera.camera.GetNextImage()
        if image_result.IsIncomplete():
            print(
                "Image incomplete with image status %d ..."
                % image_result.GetImageStatus()
            )
        else:
            d = image_result.GetNDArray()
            print(d)
        time.sleep(1)
        # print("setcont")
        self.camera.startWorker()
        # self.setContinuous()

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
