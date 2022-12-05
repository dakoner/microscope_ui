import time
from PyQt5 import QtCore
import json
import simplejpeg
import imagezmq
import numpy as np
import sys
sys.path.append("..")
from microscope_ui.config import IMAGEZMQ, PORT



class ImageZMQCameraReader(QtCore.QThread):
    
    # stateChanged = QtCore.pyqtSignal(str)
    # posChanged = QtCore.pyqtSignal(list)
    imageChanged = QtCore.pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

        # self.m_state = None
        # self.m_pos = None
        # self.m_image = None

    def run(self):         
        message, jpg_buffer = self.image_hub.recv_jpg()
        rt, colorspace = message
        image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace=colorspace)

        while True:
            message, jpg_buffer = self.image_hub.recv_jpg()
            t0 = time.time()
            #print(t0-message)
            image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace=colorspace)
            # m = json.loads(message)

            # self.pos = m['m_pos']
            # self.state = m['state']
            self.image = image_data

    # @QtCore.pyqtProperty(str, notify=stateChanged)
    # def state(self):
    #     return self.m_state

    # @state.setter
    # def state(self, state):
    #     if self.m_state == state: return
    #     self.m_state = state
    #     self.stateChanged.emit(state) 


    # @QtCore.pyqtProperty(str, notify=posChanged)
    # def pos(self):
    #     return self.m_pos

    # @pos.setter
    # def pos(self, pos):
    #     if self.m_pos == pos: return
    #     self.m_pos = pos
    #     self.posChanged.emit(pos)


    @QtCore.pyqtProperty(str, notify=imageChanged)
    def image(self):
        return self.m_image

    @image.setter
    def image(self, image):
        self.m_image = image
        self.imageChanged.emit(image)

    