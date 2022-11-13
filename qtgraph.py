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

        data = np.load("c:\\Users\\dek\\Desktop\\data2.npy")
        self.main_window.graphicsView.setImage(data, xvals=np.linspace(1., 20., data.shape[0]))


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
  
    # Interpret image data as row-major instead of col-major
    pg.setConfigOptions(imageAxisOrder='row-major')

    app = QApplication(sys.argv)

    # # Display the data and assign each frame a time value from 1.0 to 3.0
    # imv.setImage(data, xvals=np.linspace(1., 20., data.shape[0]))
    # imv.play(10)

    # ## Set a custom color map
    # colors = [
    #     (0, 0, 0),
    #     (45, 5, 61),
    #     (84, 42, 55),
    #     (150, 87, 60),
    #     (208, 171, 141),
    #     (255, 255, 255)
    # ]
    # cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
    # imv.setColorMap(cmap)

    app.exec()


