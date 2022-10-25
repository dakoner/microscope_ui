from PyQt5 import QtWidgets, QtCore, QtGui

class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
