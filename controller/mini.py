from PyQt5 import QtGui, QtCore, QtWidgets
import signal
import sys
from image_zmq_camera_reader_direct import ImageZMQCameraReaderDirect
   
class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = QtWidgets.QMainWindow()
        self.main_window.showMaximized()
        self.image_view = QtWidgets.QLabel()
        self.main_window.setCentralWidget(self.image_view)

        self.camera = ImageZMQCameraReaderDirect()
        self.camera.imageChanged.connect(self.imageChanged)
        self.camera.start()

    def imageChanged(self, draw_data):
        image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.image_view.setPixmap(pixmap)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()

