import sys

sys.path.insert(0, "controller")
sys.path.insert(0, "../controller")
from util import get_image_data
import signal
from PyQt5 import QtGui, QtCore, QtWidgets


class ImageNode(QtWidgets.QGraphicsRectItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges
        )
        self.edges = []

    def itemChange(self, change, variant):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            pass
        return super().itemChange(change, variant)


class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)

    def resizeEvent(self, event):
        # fitInView interferes with scale()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    # load two images and calculate their overlap, then print their cross-correlation(?)
    def addItem(self, bounds):
        x, y = bounds[0], bounds[1]
        width, height = bounds[2] - x, bounds[3] - y
        r = ImageNode(-width, -height, width, height)
        self.scene.addItem(r)
        r.setPos(x, y)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0))
        pen.setWidth(10)
        r.setPen(pen)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 0))
        r.setBrush(brush)
        return r


class QApplication(QtWidgets.QApplication):
    def __init__(self, prefix, *argv):
        super().__init__(["foo"])
        self.scanned_image = ScannedImage()

        self.main_window = QtWidgets.QMainWindow()
        self.main_window.setCentralWidget(self.scanned_image)
        self.scanned_image.show()
        self.scanned_image.scene.setSceneRect(
            self.scanned_image.scene.itemsBoundingRect()
        )
        self.scanned_image.scene.clearSelection()

        self.main_window.showMaximized()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prefix = r".\controller\photo\1732835470.1956787"
    else:
        prefix = sys.argv[1]

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(prefix)
    app.exec()
