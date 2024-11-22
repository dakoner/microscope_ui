# -*- coding: utf-8 -*-

# from PySide2 import QtCore  # type: ignore
# from PySide2 import QtGui  # type: ignore
# from PySide2 import QtWidgets  # type: ignore
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
import signal


from PIL import Image
import qimage2ndarray
import sys
import numpy as np
from PyQt5.uic import loadUi



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi("stitcher/stitcher.ui", self)

class QApplication(QtWidgets.QApplication):
                     


    def __init__(self, *argv):
        super().__init__(*argv)

        self.main_window = MainWindow()
        self.main_window.show()#showMaximized()
        self.label = self.main_window.findChild(QtWidgets.QLabel, "label")
        
        
        fname = "stitcher/stitched_image.npy"
        image = np.load(fname)
        image = qimage2ndarray.array2qimage(image)#, normalize=True)
        pixmap = QtGui.QPixmap.fromImage(image)


        self.label.setPixmap(pixmap)

        # self.main_window.showMaximized()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)    
    app.exec_()
