from PyQt5 import QtWidgets, QtCore, QtGui
from config import PIXEL_SCALE

class TileWindow(QtWidgets.QGraphicsView):
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSceneRect(0, 0, 60/PIXEL_SCALE, 60/PIXEL_SCALE)
        self.app = QtWidgets.QApplication.instance()


    # def drawForeground(self, p, rect):
    #     if self.app.currentPosition is not None:
    #         p.save()
    #         p.resetTransform()
            
            
    #         pen = QtGui.QPen(QtCore.Qt.red)
    #         pen.setWidth(2)
    #         p.setPen(pen)        

    #         font = QtGui.QFont()
    #         font.setFamily('Times')
    #         font.setBold(True)
    #         font.setPointSize(12)
    #         p.setFont(font)

    #         p.drawText(0, 50, self.app.state)
    #         p.drawText(0, 100, "X%8.3fmm" % self.app.currentPosition[0])
    #         p.drawText(0, 150, "Y%8.3fmm" % self.app.currentPosition[1])
    #         p.drawText(0, 200, "Z%8.3fmm" % self.app.currentPosition[2])

    #         p.restore()