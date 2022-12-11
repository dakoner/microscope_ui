import os
import glob
import pandas as pd
import json
import numpy as np
import tifffile
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
sys.path.append("..")
from microscope_ui.config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE

class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)

        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        # fitInView interferes with scale()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_Plus:
            self.scale(2,2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.5,0.5)

    def addImage(self, pos, image):
        width = image.shape[1]
        height = image.shape[0]
        image = QtGui.QImage(image, width, height, QtGui.QImage.Format_Grayscale8)

        # r = self.scene.addRect(pos.x(), pos.y(), width, height)
        # r.setZValue(2)

        #qp = QtGui.QPainterPath()
        
        # a = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32)
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
        #         p.drawRect(x, y, width, height)
        #         p.end()
        # self.scene.removeItem(r)
        
        # image.setAlphaChannel(a)
        pixmap = QtGui.QPixmap.fromImage(image)


        pm = self.scene.addPixmap(pixmap)
        pm.setPos(pos)
        pm.setZValue(1)
        # self.scene.addRect(p)

    def save(self, prefix, t, z):
        r = self.scene.itemsBoundingRect()
        width = round(r.width())
        height = round(r.height())
        image = QtGui.QImage(width, height, QtGui.QImage.Format_ARGB32)
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



class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.show()

        self.scanned_image = ScannedImage()

        self.main_window.setCentralWidget(self.scanned_image)

        g = glob.glob("movie/*")
        g.sort()
        prefix = g[-1]
        d=json.load(open(f"{prefix}/scan_config.json"))
        r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
        for row in r.itertuples():
            fname = os.path.join(prefix, row.fname)
            if os.path.exists(fname):
                data = tifffile.imread(fname)
                x0 = row.x / PIXEL_SCALE
                y0 = row.y / PIXEL_SCALE*2
                print(x0, y0)
                self.scanned_image.addImage(QtCore.QPoint(x0, y0), data)


        self.scanned_image.scene.setSceneRect(self.scanned_image.scene.itemsBoundingRect())

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()