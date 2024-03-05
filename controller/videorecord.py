import time
import ffmpeg
import mvsdk
from collections import deque
from statistics import mean

class GigECamera():
    

    def __init__(self, parent=None):

        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return
            
        for i, DevInfo in enumerate(DevList):
            print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
        i = 0 if nDev == 1 else int(input("Select camera: "))
        DevInfo = DevList[i]

        
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message) )
            return


        self.times = deque()

    @mvsdk.method(mvsdk.CAMERA_SNAP_PROC)
    def callback(self, hCamera, pRawData, pFrameHead, pContext):
        t0 = time.time()
        self.times.append(t0 - self.t0)
        self.t0 = t0
        if len(self.times) > 10:
            self.times.popleft()
        print(1./mean(self.times))

        FrameHead = pFrameHead[0]
        pFrameBuffer = self.pFrameBuffer

        mvsdk.CameraImageProcess(hCamera, pRawData, pFrameBuffer, FrameHead)
        mvsdk.CameraReleaseImageBuffer(hCamera, pRawData)

        frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(pFrameBuffer)
        self.process.stdin.write(frame_data)
        #self.data.write(frame_data)
        
    def begin(self):
        self.cap = mvsdk.CameraGetCapability(self.hCamera)

        monoCamera = (self.cap.sIspCapacity.bMonoSensor != 0)
        if monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        self.FrameBufferSize = self.cap.sResolutionRange.iWidthMax * self.cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(self.FrameBufferSize, 16)

        print("td", mvsdk.CameraGetTriggerDelayTime(self.hCamera))
        mvsdk.CameraSetStrobeMode(self.hCamera, 1)
        print("sm ", mvsdk.CameraGetStrobeMode(self.hCamera))
               
        mvsdk.CameraSetStrobeDelayTime(self.hCamera, 0)
        print("sd", mvsdk.CameraGetStrobeDelayTime(self.hCamera))
        mvsdk.CameraSetStrobePulseWidth(self.hCamera, 50000)
        print("sw", mvsdk.CameraGetStrobePulseWidth(self.hCamera))
        print("sp", mvsdk.CameraGetStrobePolarity(self.hCamera))
        mvsdk.CameraSetExtTrigSignalType(self.hCamera, 1)
        print("et", mvsdk.CameraGetExtTrigSignalType(self.hCamera))
        print("et", mvsdk.CameraGetExtTrigDelayTime(self.hCamera))
        print("etj", mvsdk.CameraGetExtTrigJitterTime(self.hCamera))
        print("tc", mvsdk.CameraGetTriggerCount(self.hCamera))


        self.ExposureTime = mvsdk.CameraGetExposureTime(self.hCamera)
        print("ex", mvsdk.CameraGetExtTrigSignalType(self.hCamera))
        #self.ExposureTime = 0
        self.Gamma = mvsdk.CameraGetGamma(self.hCamera)
        self.Contrast = mvsdk.CameraGetContrast(self.hCamera)
        self.Sharpness = mvsdk.CameraGetSharpness(self.hCamera)
        self.AnalogGain = mvsdk.CameraGetAnalogGain(self.hCamera)

        self.VMirror = mvsdk.CameraGetMirror(self.hCamera, 1)
        self.HMirror = mvsdk.CameraGetMirror(self.hCamera, 0)
        self.TriggerMode = mvsdk.CameraGetTriggerMode(self.hCamera)
        #self.AeState = mvsdk.CameraGetAeState(self.hCamera)
        #self.AeState = True
        self.AeTarget = mvsdk.CameraGetAeTarget(self.hCamera)
        print("Disable autoexposure")
        mvsdk.CameraSetAeState(self.hCamera, False)
        mvsdk.CameraSetExposureTime(self.hCamera, 1)

        
        self.enableCallback()
        self.t0 = time.time()

    def enableCallback(self):
        mvsdk.CameraSetCallbackFunction(self.hCamera, self.callback, 0)
    def disableCallback(self):
        mvsdk.CameraSetCallbackFunction(self.hCamera, None, 0)


    def end(self):
        self.disableCallback()
        
        mvsdk.CameraUnInit(self.hCamera)
        mvsdk.CameraAlignFree(self.pFrameBuffer) 


    def camera_play(self):
        return mvsdk.CameraPlay(self.hCamera)


    def camera_stop(self):
        return mvsdk.CameraStop(self.hCamera)


    def getFrameStatistic(self):
        return mvsdk.CameraGetFrameStatistic(self.hCamera)

    def cameraSoftTrigger(self):
        return mvsdk.CameraSoftTrigger(self.hCamera)


    def record(self):
        #self.data = open("file.bin", "wb")

        self.process = (
        ffmpeg
            .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(1280, 1024))
            .output("movie.mp4",  vcodec='libx264', preset="ultrafast", crf=30, threads=1)
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

    def stop_record(self):
        self.process.stdin.close()
        self.process.wait()
        #self.data.close()

if __name__ == '__main__':
    camera = GigECamera()
    camera.begin()
    camera.record()
    camera.camera_play()

    while True:
        time.sleep(0.1)
        
