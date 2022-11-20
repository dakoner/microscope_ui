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
from microscope_ui.config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS

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

        image = QtGui.QImage(image, width, height, QtGui.QImage.Format_RGB888)

        # r = self.scene.addRect(pos.x(), pos.y(), width, height)
        # qp = QtGui.QPainterPath()
        
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
        
        #image.setAlphaChannel(a)
        pixmap = QtGui.QPixmap.fromImage(image)


        pm = self.scene.addPixmap(pixmap)
        pm.setPos(pos)
        pm.setZValue(2)

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
        self.tab_widget = QtWidgets.QTabWidget(self.main_window)
        self.tab_widget.show()
        self.main_window.setCentralWidget(self.tab_widget)

        g = glob.glob("movie/*")
        g.sort()
        prefix = g[-1]
        d=json.load(open(f"{prefix}/scan_config.json"))
        r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
        r.set_index(['counter', 'i', 'j', 'k'])

        x_max = d['k_dim']*FOV_X_PIXELS+WIDTH
        y_max = d['j_dim']*FOV_Y_PIXELS+HEIGHT
        z_max = d['i_dim']
        print(r.counter.unique())
        for t in r.counter.unique()[:-1]:
            print("t=",t)
            inner_tab_widget = QtWidgets.QTabWidget(self.tab_widget)
            inner_tab_widget.show()
            self.tab_widget.addTab(inner_tab_widget, f"t={t}")

            # Get all items in time t
            all_t = r[r.counter == t]

            # We now have all the CZYX data for a time    
            for i in range(d['i_dim']):
                all_ti = all_t[all_t.i == i]
                print("\t", "z=",i)
                
                scanned_image = ScannedImage()
                inner_tab_widget.addTab(scanned_image, f"z={i}")
                for row in all_ti.itertuples():
                    fname = row.fname
                    data = tifffile.imread(os.path.join(prefix, row.fname))
                    x0 = row.k * FOV_X_PIXELS
                    y0 = row.j * FOV_Y_PIXELS
                    x1 = x0 + WIDTH
                    y1 = y0 + HEIGHT
                    scanned_image.addImage(QtCore.QPoint(x0, y0), data)

            
                #     for c in range(3):
                #         pass
                # for c in range(3):
                #     #out_fname = f"chimerax\\image_{t}_{c}_{i}.tiff"
                #     out_fname="chimerax\\" + f"image_{t}_{i}_{c}.tif"
                #     tifffile.imwrite(out_fname, o[c])

                scanned_image.scene.setSceneRect(scanned_image.scene.itemsBoundingRect())
                scanned_image.save("chimerax", t, i)
        self.main_window.show()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()