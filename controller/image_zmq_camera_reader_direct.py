from PyQt5 import QtCore
import numpy as np
import time
import cv2

class ImageZMQCameraReaderDirect(QtCore.QThread):  
    imageChanged = QtCore.pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.m_image = None

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

    def run(self):  
        t0 = time.time()    
        counter =0
        while True:
                ret, img = self.cap.read()
                if ret:
                    t1 = time.time()
                    if t1 - t0 >= 0.1:
                        self.image = img
                        t0 = t1
                counter += 1

    @QtCore.pyqtProperty(str, notify=imageChanged)
    def image(self):
        return self.m_image

    @image.setter
    def image(self, image):
        self.m_image = image
        self.imageChanged.emit(image)

    