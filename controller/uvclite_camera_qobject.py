import numpy as np
from PyQt6 import QtCore
import uvclite
from config import WIDTH, HEIGHT, FPS
import numpy as np
import cv2

class Worker(QtCore.QThread):
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)

    def __init__(self, device):
        super().__init__()
        self.device = device
        self.paused = False
        self.device.start_streaming()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    @QtCore.pyqtSlot()
    def run(self):
        while not self.paused:
            self.acquire_callback()

    def acquire_callback(self):
        frame = self.device.get_frame()
        print(frame.size)  # print size of frame in bytes
        if frame.size != 1280*720*2:
            print("bad frame")
            return
        raw_data = np.frombuffer(frame.data, dtype=np.uint8, count=1280*720*2)
        im = raw_data.reshape(720, 1280, 2)
        self.imageChanged.emit(
            cv2.cvtColor(im, cv2.COLOR_YUV2BGR_YUYV),
            1280, 720, 1280
        )

    def __del__(self):
        self.device.stop_streaming()
        self.device.close()


class UVCCamera(QtCore.QObject):

    exposureChanged = QtCore.pyqtSignal(float)
    autoExposureModeChanged = QtCore.pyqtSignal(bool)
    acquisitionModeChanged = QtCore.pyqtSignal(bool)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    snapshotCompleted = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context = uvclite.UVCContext()
        self.device = self.context.find_device() # finds first device
        self.device.open()
        self.device.print_diagnostics()
        devdesc = self.device.get_device_descriptor()
        print("Vendor ID: %d" % devdesc.idVendor)
        print("Product ID: %d" % devdesc.idProduct)
        print("UVC Standard: %d" % devdesc.bcdUVC)
        print("Serial Number: %s" % devdesc.serialNumber)
        print("Manufacturer: %s" % devdesc.manufacturer)
        print("Product Name %s" % devdesc.product)
        # print(uvclite.libuvc.uvc_get_format_descs)
        # format_desc = uvclite.libuvc.uvc_get_format_descs(device._handle_p)
        # print(format_desc)
        self.device.set_stream_format(uvclite.UVCFrameFormat.UVC_FRAME_FORMAT_YUYV, width=1280, height=720)  # sets default format (MJPEG, 640x480, 30fps)
        self.worker = None 

    def __del__(self):
        self.device.free_device_descriptor()
        print("Freed descriptor")

    def callback(self, d, w, h, s):
        self.currentFrame = d
        self.imageChanged.emit(d, w, h, s)

    def snapshot(self):
        self.snapshotCompleted.emit(self.currentFrame)

    def camera_play(self):
        pass

    def enableCallback(self):
        print("enableCallback")
        # self.worker.resume()

    def disableCallback(self):
        print("disableCallback")
        # self.worker.pause()

    def begin(self):
        self.worker = Worker(self.device)
        self.worker.imageChanged.connect(self.callback)#, QtCore.Qt.DirectConnection)
        self.worker.start()

    def end(self):
        self.worker.terminate()
        self.worker = None
        self.cap.release()

    # @QtCore.pyqtProperty(str, notify=acquisitionModeChanged)
    # def acquisitionMode(self):
    #     return self.camera.AcquisitionMode.ToString()

    # @acquisitionMode.setter
    # def acquisitionMode(self, acquisitionMode):
    #     node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('AcquisitionMode'))
    #     acquisitionMode_value = node_acquisition_mode.GetEntryByName(acquisitionMode).GetValue()
    #     if acquisitionMode_value == node_acquisition_mode.GetIntValue(): return
    #     node_acquisition_mode.SetIntValue(acquisitionMode_value)
    #     self.acquisitionModeChanged.emit(node_acquisition_mode.GetIntValue())

    # @QtCore.pyqtProperty(bool)#, notify=autoExposureModeChanged)
    # def autoExposureMode(self):
    #     try:
    #         node_autoExposure_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode('ExposureAuto'))
    #         currentValue = node_autoExposure_mode.GetIntValue()
    #         if currentValue == PySpin.ExposureAuto_Off: returnValue= False
    #         elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
    #         return returnValue
    #     except:
    #         import traceback
    #         traceback.print_exc()

    # @autoExposureMode.setter
    # def autoExposureMode(self, autoExposureMode):
    #     currentValue = self.camera.ExposureAuto.GetValue()
    #     if autoExposureMode is False:
    #         if currentValue is PySpin.ExposureAuto_Off: return
    #         self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)

    #     elif autoExposureMode is True:
    #         if currentValue is PySpin.ExposureAuto_Continuous: return
    #         self.camera.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)

    #     currentValue = self.camera.ExposureAuto.GetValue()

    #     if currentValue == PySpin.ExposureAuto_Off: returnValue= False
    #     elif currentValue == PySpin.ExposureAuto_Continuous: returnValue= True
    #     self.autoExposureModeChanged.emit(returnValue)

    # @QtCore.pyqtProperty(float, notify=exposureChanged)
    # def exposure(self):
    #     return self.camera.ExposureTime.GetValue()

    # @exposure.setter
    # def exposure(self, exposure):
    #     print("Autoexposure value:",  self.camera.ExposureAuto.GetValue())
    #     if exposure == self.camera.ExposureTime.GetValue():
    #         return
    #     self.camera.ExposureTime.SetValue(exposure)
    #     self.exposureChanged.emit(self.camera.ExposureTime.GetValue())
