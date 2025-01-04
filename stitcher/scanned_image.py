import sys
import concurrent.futures
import pathlib
from tile_configuration import TileConfiguration
import os
import glob
import qimage2ndarray
import numpy as np
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets

sys.path.insert(0, "controller")
sys.path.insert(0, "../controller")
from config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE
from PIL import Image


class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)

        # self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        # self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        # fitInView interferes with scale()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        key = event.key()
        # check if autorepeat (only if doing cancelling-moves)
        if key == QtCore.Qt.Key_Plus:
            self.scale(2, 2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.5, 0.5)

    def addImage(self, pos, image):
        # r = self.scene.addRect(pos.x(), pos.y(), image.width(), image.height())
        # r.setZValue(2)

        # qp = QtGui.QPainterPath()

        # a = QtGui.QImage(image.width(), image.height(), QtGui.QImage.Format_ARGB32)
        # a.fill(QtGui.QColor(255, 255, 255, 255))

        # qp.addRect(r.sceneBoundingRect())
        # for item in r.collidingItems():
        #     qp2 = QtGui.QPainterPath()
        #     if isinstance(item, QtWidgets.QGraphicsPixmapItem):
        #         qp2.addRect(item.sceneBoundingRect())
        #         qp3 = qp.intersected(qp2)
        #         qp3.closeSubpath()
        #         x = qp3.boundingRect().x()-pos.x()
        #         y = qp3.boundingRect().y()-pos.y()
        #         width = qp3.boundingRect().width()
        #         height = qp3.boundingRect().height()
        #         if width < height:
        #             linearGrad = QtGui.QLinearGradient(0, 0, width, 1)
        #         else:
        #             linearGrad = QtGui.QLinearGradient(0, 0, 1, height)

        #         linearGrad.setColorAt(0, QtGui.QColor(0, 0, 0, 255))
        #         linearGrad.setColorAt(1, QtGui.QColor(255, 255, 255, 255))
        #         p = QtGui.QPainter()
        #         p.begin(a)
        #         p.setPen(QtCore.Qt.NoPen)
        #         p.setBrush(QtGui.QBrush(linearGrad))
        #         p.drawRect(int(x), int(y), int(width), int(height))
        #         p.end()
        # self.scene.removeItem(r)

        # image.setAlphaChannel(a)
        pixmap = QtGui.QPixmap.fromImage(image)
        pm = self.scene.addPixmap(pixmap)
        #pm.setOpacity(0.5)
        pm.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable)
        pm.setPos(pos)
        pm.setZValue(1)
        # self.scene.addRect(p)
        return pm

    def save(self, prefix, t, z):
        r = self.scene.itemsBoundingRect()
        width = round(r.width())
        height = round(r.height())
        image = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32_Premultiplied)
        image = image.mirrored(horizontal=True, vertical=False)
        p = QtGui.QPainter(image)
        self.scene.render(p)
        p.end()

        ptr = image.bits()
        ptr.setsize(width * height * 4)
        arr = np.frombuffer(ptr, np.ubyte).reshape(height, width, 4)

        # fname = os.path.join(prefix, f"image_{t}_{z}.tif")
        # image.save(fname)

        for c in 0, 1, 2:
            fname = os.path.join(prefix, f"image_t={t}_z={z}_c={c}.tif")
            r = arr[:, :, c]
            tifffile.imwrite(fname, r)


def get_image_data(filename):
    im = Image.open(filename)
    #im = im.convert("L")
    return np.asarray(im)


class QApplication(QtWidgets.QApplication):
    def doit(self):
        prefix = pathlib.Path(
            sys.argv[1]
        )

        self.tc = TileConfiguration()
        self.tc.load(prefix / "TileConfiguration.txt")
        self.tc.move_to_origin()

        # for image in self.tc.images:
        #     print(image.filename)
        #     self.images[image.filename] = get_image_data(prefix / image.filename)
        self.items = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = {
                executor.submit(
                    get_image_data, pathlib.Path(prefix) / image.filename
                ): image
                for image in self.tc.images
            }

            for future in concurrent.futures.as_completed(futures):
                image = futures[future]
                img = future.result()
                img = qimage2ndarray.array2qimage(img)
                img.convertTo(QtGui.QImage.Format.Format_ARGB32)
                #img = img.mirrored(horizontal=True, vertical=True)
                x0 = image.x
                y0 = image.y
                pm = self.scanned_image.addImage(QtCore.QPoint(int(x0), int(y0)), img)
                self.items[pm] = x0, y0

    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.show()  # Maximized()

        self.dock = QtWidgets.QDockWidget()

        self.dock_widget = QtWidgets.QWidget()
        self.dock_layout = QtWidgets.QVBoxLayout()

        self.dock_widget.setLayout(self.dock_layout)

        self.x_button = QtWidgets.QDoubleSpinBox()
        self.x_button.setRange(0.80, 1.4)
        self.x_button.setSingleStep(0.001)
        self.x_button.setValue(1.0)
        self.x_button.setDecimals(3)
        self.x_button.valueChanged.connect(self.updatePositions)
        self.dock_layout.addWidget(self.x_button)

        self.y_button = QtWidgets.QDoubleSpinBox()
        self.y_button.setRange(0.80, 1.4)
        self.y_button.setSingleStep(0.001)
        self.y_button.setValue(1.0)
        self.y_button.setDecimals(3)
        self.y_button.valueChanged.connect(self.updatePositions)
        self.dock_layout.addWidget(self.y_button)

        # setting widget to the dock
        self.dock.setWidget(self.dock_widget)
        # self.dock.setGeometry(100, 0, 200, 30)

        self.scanned_image = ScannedImage()

        self.main_window.setCentralWidget(self.scanned_image)
        self.main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock)
        self.doit()

        self.scanned_image.scene.setSceneRect(
            self.scanned_image.scene.itemsBoundingRect()
        )
        self.scanned_image.scene.clearSelection()

        # image = QtGui.QImage(self.scanned_image.scene.sceneRect().size().toSize(), QtGui.QImage.Format_RGB888);
        # image.fill(QtCore.Qt.transparent);

        # painter = QtGui.QPainter (image);

        # painter.begin(image)
        # self.scanned_image.scene.render(painter);
        # image.save("file_name.png")
        # painter.end()

    def updatePositions(self, arg):
        for item in self.scanned_image.scene.items():
            if type(item) == QtWidgets.QGraphicsPixmapItem:
                x, y = self.items[item]
                pos_x = x / PIXEL_SCALE * self.x_button.value()
                pos_y = y / PIXEL_SCALE * self.y_button.value()
                item.setPos(pos_x, pos_y)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.exec()
