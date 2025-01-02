import numpy as np
from PyQt6 import QtCore, QtGui
from config import WIDTH, HEIGHT, FPS
import numpy as np
import QUVCObject
import ffmpeg

class QUVCObjectCamera(QtCore.QObject):

    ExposureTimeChanged = QtCore.pyqtSignal(float)
    AeStateChanged = QtCore.pyqtSignal(float)
    AnalogGainChanged = QtCore.pyqtSignal(float)
    imageChanged = QtCore.pyqtSignal(QtGui.QImage)
    yuvImageChanged = QtCore.pyqtSignal(np.ndarray, int, int, int)
    snapshotCompleted = QtCore.pyqtSignal(QtGui.QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.q = QUVCObject.QUVCObject()
        self.d = QUVCObject.UVCDevice()
        self.q.find_device(self.d, 0x4b4, 0x477, None)
        self.dh = QUVCObject.UVCDeviceHandle()
        self.q.open_device(self.d, self.dh)
        self.q.frameChanged.connect(self.callback)
        self.q.yuvFrameChanged.connect(self.yuv_callback)
        self.process = None

    def get_exposure_abs_cur(self):
        return self.q.get_exposure_abs(self.dh, bytearray.fromhex('81'))
 
    def get_exposure_abs_min(self):
        return self.q.get_exposure_abs(self.dh, bytearray.fromhex('82'))
 
    def get_exposure_abs_max(self):
        return self.q.get_exposure_abs(self.dh, bytearray.fromhex('83'))

        
    @QtCore.pyqtProperty(float, notify=ExposureTimeChanged)
    def ExposureTime(self):
        return self.get_exposure_abs_cur()
                                                    
    @ExposureTime.setter
    def ExposureTime(self, exposure):
        if exposure == self.get_exposure_abs_cur():
            return
        result = self.q.set_exposure_abs(self.dh, exposure)
        return self.get_exposure_abs_cur()
 
    def get_ae_mode(self):
        return self.q.get_ae_mode(self.dh, bytearray.fromhex('81'))
 
    
    @QtCore.pyqtProperty(int, notify=AeStateChanged)
    def AeState(self):
        return self.get_ae_mode_cur()

    @AeState.setter
    def AeState(self, state):
        if state == self.get_ae_mode_cur():
            return
        result = self.q.set_ae_mode(self.dh, state)
        return self.get_ae_mode_cur()
    
    
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
 
    def yuv_callback(self, frame, width, height, data_bytes):
    
        if self.process:
            frame.setsize(data_bytes*2)
            assert (data_bytes * 2 == width*height*2)
            self.process.stdin.write(frame.asstring())
        

    def callback(self, image):
        #print("callback")
        #image = qimage.convertToFormat(QtGui.QImage.Format.Format_ARGB32)
        # d = qimage2ndarray.rgb_view(i).copy()
        self.currentFrame = image
        self.imageChanged.emit(image)#d, d.shape[1], d.shape[0], d.shape[1])
        
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

    def startRecording(self, fname):
        if self.process:
            print("Already recording")
            return
        # ffmpeg -f rawvideo -pix_fmt yuyv422 -s 1280x720 -i test.raw  -vcodec libx264 -pix_fmt yuv420p  movie.mp4 -y
        self.process = (
            ffmpeg.input(
                "pipe:",
                format="rawvideo",
                pix_fmt="yuyv422",
                s="{}x{}".format(1280, 720),
            )
            .output(
                fname, pix_fmt="yuv422", vcodec="libx264"
            )  
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

    def stopRecording(self):
        if self.process:
            self.process.stdin.close()
            self.process = None
        
    def begin(self):
        format = 3
        print(self.dh)
        self.q.stream(self.dh, format, 1280, 720, 120)

    def end(self):
        pass
