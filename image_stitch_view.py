import os
from glob import glob
import traceback
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets, QtSvg
import glob



class MainWindow(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QtWidgets.QGraphicsScene(self)
        #self.scene.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(131, 213, 247)))
        #self.scene.setSceneRect(0, 0, WIDTH, HEIGHT)

        #self.machine = QtSvg.QGraphicsSvgItem('../static/assets/burger_chute.svg')
        #self.scene.addItem(self.machine)
        #self.machine.setScale(2)
        #self.machine.setPos(1000,0)
 
        #self.setFixedSize(WIDTH,HEIGHT)
        self.setScene(self.scene)
        #self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        x_const = -2175
        y_const = +1900
        fnames = sorted(glob.glob("movie_grayscale/*.jpg"))
        for fname in fnames:
            f = os.path.basename(fname)[:-4].split("_")
            image = QtGui.QImage(fname)
            pixmap = QtGui.QPixmap.fromImage(image)
            pixmap = self.scene.addPixmap(pixmap)
            pixmap.setOpacity(0.5)
            pixmap.setPos(QtCore.QPointF(float(f[1])*x_const, float(f[0])*y_const))

        self.scene.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.scene and isinstance(event, QtWidgets.QGraphicsSceneMouseEvent):
            if (event.buttons() & QtCore.Qt.LeftButton):
                item = self.scene.itemAt(event.scenePos(), QtGui.QTransform())
                item.setPos(item.pos() + (event.scenePos() - event.lastScenePos()))
                return True
            else:
                return super().eventFilter(obj, event)
        else:
            return super().eventFilter(obj, event)
            

#             QPointF delta = m->lastScreenPos() - m->screenPos();
#             int newX = view->horizontalScrollBar()->value() + delta.x();
#             int newY = view->verticalScrollBar()->value() + delta.y();
#             view->horizontalScrollBar()->setValue(newX);
#             view->verticalScrollBar()->setValue(newY);
#             return true;
#         }
#     }

#     return QMainWindow::eventFilter(obj, event);
# }
                

class QApplication(QtWidgets.QApplication):
    def __init__(self, *args, **kwargs):
        super(QApplication, self).__init__(*args, **kwargs)
    def notify(self, obj, event):
        try:
            return QtWidgets.QApplication.notify(self, obj, event)
        except Exception:
            print(traceback.format_exception(*sys.exc_info()))
            return False
        
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    #widget.showFullScreen()
    app.exec_()