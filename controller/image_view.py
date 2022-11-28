import time
import sys
sys.path.append("..")
from microscope_ui.config import PIXEL_SCALE, TARGET, XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE, HEIGHT, WIDTH, FOV_X, FOV_Y
from PyQt5 import QtWidgets, QtCore, QtGui

class ImageView(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFocusPolicy(True)        

    def keyPressEvent(self, event):
 
        app = QtWidgets.QApplication.instance()
        self.client = app.client
        self.camera = app.camera
        self.scene = app.main_window.tile_graphics_view.scene
        key = event.key()  
        # check if autorepeat (only if doing cancelling-moves)  
        if key == QtCore.Qt.Key_C:
            self.client.publish(f"{TARGET}/cancel", "")
        if key == QtCore.Qt.Key_H:
            self.client.publish(f"{TARGET}/command", "$H")
        elif key == QtCore.Qt.Key_S:
            self.client.publish(f"{TARGET}/cancel", "")
            app.main_window.tile_graphics_view.stopAcquisition()
        elif key == QtCore.Qt.Key_P:
            app=QtWidgets.QApplication.instance()
            camera = app.camera
            draw_data = camera.image
            pos = camera.pos
            fname = f"image_{int(time.time())}.tif"
            image = QtGui.QImage(draw_data, draw_data.shape[1], draw_data.shape[0], QtGui.QImage.Format_RGB888)
            image.save(fname)
        elif key == QtCore.Qt.Key_R:
            self.scene.clear()
            app.main_window.tile_graphics_view.addStageRect()
            app.main_window.tile_graphics_view.addCurrentRect()

        elif self.camera.state == "Idle":
            if key == QtCore.Qt.Key_Left:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Right:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Up:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_Down:
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_PageUp:
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
            elif key == QtCore.Qt.Key_PageDown:
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}"
                self.client.publish(f"{TARGET}/command", cmd)
        return super().keyPressEvent(event)

       