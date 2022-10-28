from PyQt5 import QtCore, QtWidgets, QtGui
from config import XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE, TARGET


class ImageWindow(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = QtWidgets.QApplication.instance()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setScaledContents(True)

    # def keyReleaseEvent(self, event):
    #     key = event.key()    
    #     if key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Plus, QtCore.Qt.Key_Minus):
    #         self.app.client.publish(f"{TARGET}/cancel", "")

    def keyPressEvent(self, event):
        print("keytpress")
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_C:
            print("cancel")
            self.app.client.publish(f"{TARGET}/cancel", "")
        elif key == QtCore.Qt.Key_S:
            print("stop")
            self.app.grid = []
        elif key == QtCore.Qt.Key_P:
            print("Take photo")
            fname = "image.%08.3f,%08.3f.png" % (self.app.scale_pos[1], self.app.scale_pos[0])
            if self.app.currentImage:
                self.app.currentImage.convertToFormat(QtGui.QImage.Format_Grayscale8).save("photo/" + fname)
        elif self.app.state == "Idle":
            if key == QtCore.Qt.Key_Left:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                self.app.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Right:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                self.app.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Up:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                self.app.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Down:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                self.app.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Plus:
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                self.app.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Minus:
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                self.app.client.publish(f"{TARGET}/command", cmd)
