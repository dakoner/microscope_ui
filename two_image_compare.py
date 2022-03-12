import traceback
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets, QtSvg




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

        
        image = QtGui.QImage("movie/-000.138_-000.221.jpg")
        pixmap = QtGui.QPixmap.fromImage(image)
        pixmap = self.scene.addPixmap(pixmap)
        pixmap.setOpacity(0.5)
        pixmap.setPos(QtCore.QPointF(0, 0))

        
        image = QtGui.QImage("movie/-000.138_-000.471.jpg")
        pixmap = QtGui.QPixmap.fromImage(image)
        pixmap = self.scene.addPixmap(pixmap)
        pixmap.setOpacity(0.5)
        pixmap.setPos(QtCore.QPointF(500, 0))

        self.scene.installEventFilter(self)
        #self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
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
