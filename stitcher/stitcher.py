import dask.array as da
import pandas as pd
import tifffile
import numpy as np
import glob
import json
import sys
sys.path.append("..")
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import os
from PyQt5.uic import loadUi
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.



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

        self.main_window = QtWidgets.QTabWidget()
        self.main_window.show()
        self.load()

    def load(self):
        g = glob.glob("movie/*")
        g.sort()
        #prefix = g[-2]
        prefix="movie/1669690354.4376109"
        #print(prefix)
        d=json.load(open(f"{prefix}/scan_config.json"))
        r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
        r.set_index(['counter', 'i', 'j', 'k'])

        for t in r.counter.unique()[:-1]:
            # print(t)
            # Get all items in time t
            d = r[r.counter == t]
            data = None
            for z in d.i.unique():
                print("z=", z, "of", len(d.i.unique()))
                d2 = d[d.i == z]
                scene = QtWidgets.QGraphicsScene()
                for row in d2.itertuples():
                    fname = os.path.join(prefix, row.fname)
                    #print(row)
                    if row.k == 0:
                        continue
                    x0 = row.k * FOV_X_PIXELS
                    y0 = row.j * FOV_Y_PIXELS
                    image = QtGui.QImage(fname)
                    pixmap = QtGui.QPixmap(image)
                    item = scene.addPixmap(pixmap)
                    item.setPos(x0, y0)
                
            
                tw = TileView()
                tw.setScene(scene)
                #self.main_window.addTab(tw, f"t={t}_z={z}")           


                rect = scene.itemsBoundingRect()
                width = round(rect.width())
                height = round(rect.height())
                
                w = 16384
                h = 16384
                fullheight = height+h
                fullwidth = width+w
                
                if data is None:
                    data = np.zeros((len(d.i.unique()), fullheight, fullwidth), dtype=np.uint8)

                ys = np.arange(0, fullheight, h)
                xs = np.arange(0, fullwidth, w)
                n = np.array(np.meshgrid(xs, ys)).T.reshape(-1,2)


                for x, y in n:
                    image = QtGui.QImage(w, h, QtGui.QImage.Format_Grayscale8)
                    p = QtGui.QPainter(image)
                    scene.render(p, source=QtCore.QRectF(x, y, w, h), target=QtCore.QRectF(0, 0, w, h))
                    p.end()
                    
                    ptr = image.bits()
                    ptr.setsize(w * h)
                    arr = np.frombuffer(ptr, np.ubyte).reshape(h, w)
                    try:
                        data[z,y:y+h,x:x+w] = arr
                    except ValueError:
                        pass
                        #print(d.shape, x, y, x+h, y+h, d[y:y+h,x:x+w].shape, arr.shape)


            # out_fname = f"out/image_t={t}.npz"
            # print("save", out_fname)
            # np.savez_compressed(out_fname, data=data)
            d = da.from_array(data, chunks=(1, 32768, 32768))
            out_fname = f"out/image_t={t}.zarr"
            d.to_zarr(out_fname)
            print("done", out_fname)
        pass

                
   
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.exec_()