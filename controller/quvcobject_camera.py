import numpy as np
from PyQt6 import QtCore, QtGui
from config import WIDTH, HEIGHT, FPS
import numpy as np
import QUVCObject
import qimage2ndarray


class QUVCObjectCamera(QtCore.QObject):

    ExposureTimeChanged = QtCore.pyqtSignal(float)
    AeStateChanged = QtCore.pyqtSignal(float)
    AnalogGainChanged = QtCore.pyqtSignal(float)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    yuvImageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    snapshotCompleted = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.q = QUVCObject.QUVCObject()
        self.d = QUVCObject.UVCDevice()
        self.q.find_device(self.d, 0x4b4, 0x477, None)
        self.dh = QUVCObject.UVCDeviceHandle()
        self.q.open_device(self.d, self.dh)
        self.q.frameChanged.connect(self.callback)

    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return self._uvc_get_exposure_abs_cur()
                                                    
    @ExposureTime.setter
    def ExposureTime(self, exposure):
        if exposure == self._uvc_get_exposure_abs_cur():
            return
        result = uvclite.libuvc.uvc_set_exposure_abs(self.device._handle_p, exposure)
        return self._uvc_get_exposure_abs_cur()
 
    
    @QtCore.pyqtProperty(int, notify=AeStateChanged)
    def AeState(self):
        return self._uvc_get_ae_mode(uvclite.libuvc.uvc_req_code.UVC_GET_CUR)

    @AeState.setter
    def AeState(self, state):
        if state == self._uvc_get_ae_mode(uvclite.libuvc.uvc_req_code.UVC_GET_CUR):
            return
        result = uvclite.libuvc.uvc_set_ae_mode(self.device._handle_p, not state)
        return self._uvc_get_ae_mode(uvclite.libuvc.uvc_req_code.UVC_GET_CUR)
    
    
    # @QtCore.pyqtProperty(float, notify=AeTargetChanged)
    # def AeTarget(self):
    #     return mvsdk.CameraGetAeTarget(self.hCamera)

    # @AeTarget.setter
    # def AeTarget(self, target):
    #     if target == mvsdk.CameraGetAeTarget(self.hCamera):
    #         return
    #     mvsdk.CameraSetAeTarget(self.hCamera, target)
    #     self.AeTargetChanged.emit(mvsdk.CameraGetAeTarget(self.hCamera))


    @QtCore.pyqtProperty(int, notify=AnalogGainChanged)
    def AnalogGain(self):
        g = self._uvc_get_gain_cur()
        return g

    @AnalogGain.setter
    def AnalogGain(self, gain):
        if gain == self._uvc_get_gain_cur():
            return
        result = uvclite.libuvc.uvc_set_gain(self.device._handle_p, gain)
        return self._uvc_get_gain_cur()
 
    def callback(self, qimage):
        #print("callback")
        i = qimage.convertToFormat(QtGui.QImage.Format.Format_ARGB32)
        d = qimage2ndarray.rgb_view(i).copy()
        self.currentFrame = d
        self.imageChanged.emit(d, d.shape[1], d.shape[0], d.shape[1])
        
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
        format = 3
        print(self.dh)
        self.q.stream(self.dh, format, 1280, 720, 120)

    def end(self):
        pass
