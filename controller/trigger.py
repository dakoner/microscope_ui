
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
           