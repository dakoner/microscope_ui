from PyQt5 import QtGui, QtCore, QtWidgets

class ScannedImage(QtWidgets.QGraphicsView):
    def __init__(self, width, height, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, width, height)
        self.setSceneRect(0, 0, width, height)
        self.showMaximized()
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)


    def resizeEvent(self, event):
        # fitInView interferes with scale()
        self.fitInView(self.scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def keyPressEvent(self, event):
        print("ScannedImage event")
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_Plus:
            self.scale(2,2)
        elif key == QtCore.Qt.Key_Minus:
            self.scale(0.5,0.5)

    def addImage(self, pos, image):
        a = QtGui.QImage(image.width(), image.height(),
                QtGui.QImage.Format_ARGB32)
        a.fill(QtGui.QColor(255, 255, 255, 255))
        r = self.scene.addRect(pos.x(), pos.y(), image.width(), image.height())
        qp = QtGui.QPainterPath()
        qp.addRect(r.sceneBoundingRect())
        for item in r.collidingItems():
            qp2 = QtGui.QPainterPath()
            if isinstance(item, QtWidgets.QGraphicsPixmapItem):
                qp2.addRect(item.sceneBoundingRect())
                qp3 = qp.intersected(qp2)
                qp3.closeSubpath()
                x = qp3.boundingRect().x()-pos.x()
                y = qp3.boundingRect().y()-pos.y()
                width = qp3.boundingRect().width()
                height = qp3.boundingRect().height()
                if width < height:
                    linearGrad = QtGui.QLinearGradient(0, 0, width, 1)
                else:
                    linearGrad = QtGui.QLinearGradient(0, 0, 1, height)

                linearGrad.setColorAt(0, QtGui.QColor(0, 0, 0, 255))
                linearGrad.setColorAt(1, QtGui.QColor(255, 255, 255, 255))
                p = QtGui.QPainter()
                p.begin(a)
                p.setPen(QtCore.Qt.NoPen)
                p.setBrush(QtGui.QBrush(linearGrad))
                p.drawRect(x, y, width, height)
                p.end()
                
        #z = QtWidgets.QLabel()
        #z.setPixmap(QtGui.QPixmap.fromImage(a))
        # self.tw.addTab(z, "image")
        # self.tw.showMaximized()
        #z.show()
        image.setAlphaChannel(a)
        pixmap = QtGui.QPixmap.fromImage(image)

        self.scene.removeItem(r)

        pm = self.scene.addPixmap(pixmap)
        
        pm.setPos(pos)
        pm.setZValue(2)

    def save(self, fname):
        r = self.scene.sceneRect()
        image = QtGui.QImage(r.width(), r.height(), QtGui.QImage.Format_ARGB32)
        p = QtGui.QPainter(image)
        self.scene.render(p)
        p.end()
        image.save(fname)
        print("Save done", fname)
 