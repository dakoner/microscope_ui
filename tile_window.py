from PyQt5 import QtWidgets, QtCore, QtGui
from config import PIXEL_SCALE

class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSceneRect(0, 0, 60/PIXEL_SCALE, 60/PIXEL_SCALE)

