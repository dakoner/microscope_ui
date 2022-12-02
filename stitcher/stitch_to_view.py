import dask.array as da
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
sys.path.append("..")
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS
import numpy as np



class TileView(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def keyPressEvent(self, event):
        print("tile graphics view key press event")
        key = event.key()  
        if key == QtCore.Qt.Key_Plus:
            self.scale(1.1, 1.1)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.9, 0.9)
                
class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)

        self.main_window = QtWidgets.QMainWindow()
        self.main_window.show()
        self.tab_widget = QtWidgets.QTabWidget()
        self.main_window.setCentralWidget(self.tab_widget)


        d = da.from_zarr(f"out/images.zarr")
        # CTZYX
        print(d.shape)
        for c in range(d.shape[0]):
            print("c=", c)
            for t in range(d.shape[1]):
                print("\tt=", t)
                tab_widget = QtWidgets.QTabWidget()
                self.tab_widget.addTab(tab_widget, f"t={t}")
                for z in range(d.shape[2]):
                    print("\t\tz=", z)
                    data = np.array(d[c, t, z])
                    print(data.shape)
                    scene = QtWidgets.QGraphicsScene()
                    for i in range(data.shape[0]):
                        for j in range(data.shape[1]):
                            print(i,j)
                            image = QtGui.QImage(data[i,j].tobytes(), data.shape[3], data.shape[2], QtGui.QImage.Format_Grayscale8)
                            p = QtGui.QPixmap(image)
                            pm = scene.addPixmap(p)
                            y = i * FOV_Y_PIXELS
                            x = j * FOV_X_PIXELS
                            pm.setPos(x, y)
                    q = TileView()
                    q.setScene(scene)
                    tab_widget.addTab(q, f"z={z}")
                    return
                            
                       

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()