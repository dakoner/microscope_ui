from ctypes import byref, POINTER, c_void_p, c_uint32, c_uint16
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
        #print("Frame")
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


class UVCLiteCamera(QtCore.QObject):

    ExposureTimeChanged = QtCore.pyqtSignal(float)
    AeStateChanged = QtCore.pyqtSignal(float)
    AnalogGainChanged = QtCore.pyqtSignal(float)
    imageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    snapshotCompleted = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.context = uvclite.UVCContext()
        self.device = self.context.find_device() # finds first device
        print(dir(self.device))
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

    def _uvc_get_exposure_abs(self, flag):
        t = c_uint32()
        error = uvclite.libuvc.uvc_get_exposure_abs(self.device._handle_p, byref(t), flag.value)
        if error != 0:
            raise RuntimeError(error)
        return t.value

    def _uvc_get_exposure_abs_min(self):
        return self._uvc_get_exposure_abs(uvclite.libuvc.uvc_req_code.UVC_GET_MIN)
    
    def _uvc_get_exposure_abs_max(self):
        return self._uvc_get_exposure_abs(uvclite.libuvc.uvc_req_code.UVC_GET_MAX)
    
    def _uvc_get_exposure_abs_def(self):
        return self._uvc_get_exposure_abs(uvclite.libuvc.uvc_req_code.UVC_GET_DEF)
    
    def _uvc_get_exposure_abs_cur(self):
        return self._uvc_get_exposure_abs(uvclite.libuvc.uvc_req_code.UVC_GET_DEF)
    
        
    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return self._uvc_get_exposure_abs_cur()
                                                    
    @ExposureTime.setter
    def ExposureTime(self, exposure):
        if exposure == self._uvc_get_exposure_abs_cur():
            return
        result = uvclite.libuvc.uvc_set_exposure_abs(self.device._handle_p, exposure)
        return self._uvc_get_exposure_abs_cur()
 
 
    def _uvc_get_ae_mode(self, flag):
        t = c_uint32()
        error = uvclite.libuvc.uvc_get_ae_mode(self.device._handle_p, byref(t), flag.value)
        if error != 0:
            raise RuntimeError(error)
        return t
    
    @QtCore.pyqtProperty(int, notify=AeStateChanged)
    def AeState(self):
        return self._uvc_get_ae_mode(uvclite.libuvc.uvc_req_code.UVC_GET_CUR)

    @AeState.setter
    def AeState(self, state):
        if state == self._uvc_get_ae_mode(uvclite.libuvc.uvc_req_code.UVC_GET_CUR):
            return
        result = uvclite.libuvc.uvc_set_ae_mode(self.device._handle_p, state)
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



    def _uvc_get_gain(self, flag):
        t = c_uint16()
        error = uvclite.libuvc.uvc_get_gain(self.device._handle_p, byref(t), flag.value)
        if error != 0:
            raise RuntimeError(error)
        return t.value
    
    def _uvc_get_gain_min(self):
        return self._uvc_get_gain(uvclite.libuvc.uvc_req_code.UVC_GET_MIN)
    
    def _uvc_get_gain_max(self):
        return self._uvc_get_gain(uvclite.libuvc.uvc_req_code.UVC_GET_MAX)
    
    def _uvc_get_gain_def(self):
        return self._uvc_get_gain(uvclite.libuvc.uvc_req_code.UVC_GET_DEF)
    
    def _uvc_get_gain_cur(self):
        return self._uvc_get_gain(uvclite.libuvc.uvc_req_code.UVC_GET_DEF)
    
    
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
