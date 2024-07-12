import numpy as np
#import cv2
import time
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.uic import loadUi
import serial_interface_qobject

import gige_camera_qobject
import uvc_camera_qobject
#import pyspin_camera_qobject
#from microscope_esp32_controller_serial import serial_interface_qobject as microscope_serial_qobject
from microscope_ui.config import PIXEL_SCALE, MQTT_HOST, XY_FEED
import event_filter
import sys

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("controller/microscope_controller.ui", self)
        
        #self.toolBar.actionTriggered.connect(self.test)
        #button_action.triggered.connect(self.onMyToolBarButtonClick)

        self.serial = serial_interface_qobject.SerialInterface('/dev/ttyUSB0', "dektop")
        self.serial.posChanged.connect(self.onPosChange)
        self.serial.stateChanged.connect(self.onStateChange)
        self.serial.messageChanged.connect(self.onMessageChanged)


        # self.microscope_esp32_controller_serial =microscope_serial_qobject.SerialInterface('/dev/ttyUSB1')
        # self.microscope_esp32_controller_serial.reset()
        # time.sleep(1)

        # self.microscope_esp32_controller_serial.write("P 2000000 325\n")
        # self.microscope_esp32_controller_serial.write("L1\n")
        # self.microscope_esp32_controller_serial.messageChanged.connect(self.onMessage2Changed)

        #self.camera = pyspin_camera_qobject.PySpinCamera()
        #self.camera = uvc_camera_qobject.UVCCamera("/dev/video1")
        self.camera = gige_camera_qobject.GigECamera()
        self.camera.imageChanged.connect(self.imageChanged)
        #self.setContinuous()
        #self.setTrigger()

#        self.camera.startWorker()
        self.camera.begin()
        #self.camera.camera_play()


        self.state = 'None'
        self.m_pos = [-1, -1, -1]

        self.t0 = time.time()


        self.event_filter = event_filter.EventFilter(self)
        self.installEventFilter(self.event_filter) #keyboard control


        self.buttonGroup.buttonClicked.connect(self.triggerButtonGroupClicked)
        self.swToggleRadioButton.toggled.connect(self.enableSoftwareTrigger)
        self.swTogglePushButton.pressed.connect(self.softwareTrigger)
        self.hwToggleRadioButton.toggled.connect(self.enableHardwareTrigger)
        self.radioButton_23.toggled.connect(self.enableAuto)



        # self.AeTargetSlider.valueChanged.connect(self.AeTargetChanged)
        # self.AeTargetLabel.setText(str(self.camera.AeTarget))
        # self.AeTargetSlider.setMinimum(self.camera.cap.sExposeDesc.uiTargetMin)
        # self.AeTargetSlider.setMaximum(self.camera.cap.sExposeDesc.uiTargetMax)


        # self.exposureTimeSlider.valueChanged.connect(self.ExposureTimeChanged)
        # self.exposureTimeLabel.setText(str(self.camera.ExposureTime))
        # self.exposureTimeSlider.setMinimum(self.camera.cap.sExposeDesc.uiExposeTimeMin)
        # self.exposureTimeSlider.setMaximum(self.camera.cap.sExposeDesc.uiExposeTimeMax)

        # self.analogGainSlider.valueChanged.connect(self.AnalogGainChanged)
        # self.analogGainLabel.setText(str(self.camera.AnalogGain))
        # self.analogGainSlider.setMinimum(self.camera.cap.sExposeDesc.uiAnalogGainMin)
        # self.analogGainSlider.setMaximum(self.camera.cap.sExposeDesc.uiAnalogGainMax)


        # self.camera.AeTargetChanged.connect(lambda value: self.AeTargetSlider.setValue(int(value)))
        # self.camera.ExposureTimeChanged.connect(lambda value: self.exposureTimeSlider.setValue(int(value)))
        # self.camera.AnalogGainChanged.connect(lambda value: self.analogGainSlider.setValue(int(value)))


    def enableSoftwareTrigger(self, value):
        print("toggle radio for sw:", value)
        self.swTogglePushButton.setEnabled(value)
 
    def enableHardwareTrigger(self, value):
        print("toggle radio for sw:", value)
        self.hwTogglePushButton.setEnabled(value)
        #lambda value: self.groupBox_2.setEnabled(value))

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

    def enableAuto(self, value):
        print("enableAuto", value)
        self.groupBox_6.setEnabled(value)
        self.groupBox_5.setEnabled(not value)
        self.camera.AeState = not value

    def AeTargetChanged(self, target):
        print("AeTargetChanged", target)
        self.camera.AeTarget = target

    def ExposureTimeChanged(self, exposure):
        print("ExposureTimeChanged: ", exposure)
        self.camera.ExposureTime = exposure


    def onMessage2Changed(self, *args):
        print('message2 changed', args)

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

    def imageChanged(self, draw_data):
        t0 = time.time()
        self.t0 = t0
        if self.state == 'Jog' or self.state == 'Run':
            self.tile_graphics_view.addImageIfMissing(draw_data, self.m_pos)
                #return
        s = draw_data.shape
        if s[2] == 1:
            format = QtGui.QImage.Format_Grayscale8
        elif s[2] == 3:
            format = QtGui.QImage.Format_RGB888

        image = QtGui.QImage(draw_data, s[1], s[0], format)
        image = image.mirrored(horizontal=True, vertical=False)
        self.curr_image = image
        pixmap = QtGui.QPixmap.fromImage(image)
        #self.image_view.setFixedSize(1440/2, 1080/2)
        self.image_view.setFixedSize(s[1], s[0])
        self.image_view.setPixmap(pixmap)


    def onMessageChanged(self, message):
        self.textEdit.append(message)

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
        raise RuntimeError
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
        #self.setContinuous()
        

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
        x = position.x()*PIXEL_SCALE
        y = position.y()*PIXEL_SCALE
        cmd = f"$J=G90 G21 F{XY_FEED:.3f} X{x:.3f} Y{y:.3f}\n"
        self.serial.write(cmd)

