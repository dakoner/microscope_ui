import sys
import signal
from PyQt5 import QtWidgets

sys.path.append("..")
from microscope_ui.config import PIXEL_SCALE, MQTT_HOST, TARGET, XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE, HEIGHT, WIDTH, FOV_X, FOV_Y
from main_window import MainWindow


class QApplication(QtWidgets.QApplication):
    def __init__(self, *argv):
        super().__init__(*argv)
        self.main_window = MainWindow()
        self.main_window.show()#showMaximized()

    #     self.installEventFilter(self)

    # def eventFilter(self, widget, event):
    #     if event.type() not in (QtCore.QEvent.WindowDeactivate, QtCore.QEvent.Paint, QtCore.QEvent.UpdateRequest, QtCore.QEvent.MetaCall, QtCore.QEvent.ActivationChange, QtCore.QEvent.HoverMove, QtCore.QEvent.HoverLeave, QtCore.QEvent.HoverEnter, QtCore.QEvent.ApplicationDeactivate, QtCore.QEvent.ApplicationStateChange, QtCore.QEvent.ToolTip, QtCore.QEvent.Leave,  QtCore.QEvent.FocusAboutToChange, QtCore.QEvent.CursorChange, QtCore.QEvent.ChildRemoved, QtCore.QEvent.DeferredDelete):
    #         print(widget.objectName(), event.type())
    #     return False


    def test(self, action):
        print("action", action.objectName())
        if action.objectName() == 'stopAction':
            print("STOP")
            self.cancel()
            self.main_window.tile_graphics_view.stopAcquisition()



if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)    
    app.exec()
