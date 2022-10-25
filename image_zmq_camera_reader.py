from PyQt5 import QtCore
import simplejpeg
import imagezmq
import numpy as np
from config import IMAGEZMQ, PORT


class ImageZMQCameraReader(QtCore.QThread):
    imageSignal = QtCore.pyqtSignal(str, np.ndarray)
    #predictSignal = QtCore.pyqtSignal(list)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

    def run(self):         
        message, jpg_buffer = self.image_hub.recv_jpg()
        image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')

        while True:
            message, jpg_buffer = self.image_hub.recv_jpg()
            #print("message:", message)
            image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            self.imageSignal.emit(message, image_data)