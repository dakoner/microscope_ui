import dask.array as da
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
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

        s = QtWidgets.QGraphicsScene()

        for t in 0, 1:
            print(t)
            d = da.from_zarr(f"c:/Users/dek/Desktop/out/image_t={t}.zarr")
            tab_widget = QtWidgets.QTabWidget()
            self.tab_widget.addTab(tab_widget, f"t={t}")

            w = 16384
            h = 16384
            ys = np.arange(0, d.shape[1], h)
            xs = np.arange(0, d.shape[2], w)
            n = np.array(np.meshgrid(xs, ys)).T.reshape(-1,2)
            for z in range(0,1):
                print("\t", z)
                data = np.array(d[z])
                for x, y in n:
                    rect = data[y:y+h,x:x+w]
                    image = QtGui.QImage(rect.tobytes(), rect.shape[1], rect.shape[0], QtGui.QImage.Format_Grayscale8)
                    p = QtGui.QPixmap(image)
                    pm = s.addPixmap(p)
                    pm.setPos(x, y)
                    
                q = TileView()
                q.setScene(s)
                print(d.shape[1], d.shape[2])
                q.fitInView(0, 0, d.shape[1], d.shape[2])
                tab_widget.addTab(q, f"z={z}")
            return

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()