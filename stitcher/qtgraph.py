import sys
sys.path.append("..")
import tifffile
import pyqtgraph as pg
import pandas as pd
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import signal
from PyQt5.uic import loadUi

    
class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)

        self.main_window = QtWidgets.QMainWindow()
        loadUi("qtgraph.ui", self.main_window)
        self.main_window.show()

        data = np.load("c:\\Users\\dek\\Desktop\\data.npy")
        data = data[:, 0, :, :]
        self.main_window.graphicsView.setImage(data, xvals=np.linspace(1., 20., data.shape[0]))
        self.main_window.graphicsView.play(10)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
  
    # Interpret image data as row-major instead of col-major
    pg.setConfigOptions(imageAxisOrder='row-major')

    app = QApplication(sys.argv)
    app.exec()
