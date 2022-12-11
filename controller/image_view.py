import time
import sys
from video_sender.pyspin_camera import pyspin_camera_qobject
from fluidnc_serial import serial_interface_qobject

from PyQt5 import QtGui, QtCore, QtWidgets
sys.path.append("..")
from microscope_ui.config import XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE


class ImageView(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def keyPressEvent(self, event):
        print("key press")
        app = QtWidgets.QApplication.instance()
        main_window = app.main_window
        state = main_window.state
        serial = main_window.serial
        tile_graphics_view = main_window.tile_graphics_view
        key = event.key()
         
        if key == QtCore.Qt.Key_C:
            main_window.cancel()
        elif key == QtCore.Qt.Key_H:
            main_window.cancel()
            main_window.home()
        elif key == QtCore.Qt.Key_X:
            main_window.trigger()
        elif key == QtCore.Qt.Key_U:
            main_window.unlock()
        elif key == QtCore.Qt.Key_R:
            main_window.reset()
        elif key == QtCore.Qt.Key_S:
            main_window.cancel()
            tile_graphics_view.stopAcquisition()
        elif key == QtCore.Qt.Key_P:
            fname = f"image_{int(time.time())}.tif"
            main_window.curr_image.save(fname)
            print("saved", fname)
        elif key == QtCore.Qt.Key_R:
            tile_graphics_view.reset()
            tile_graphics_view.addCurrentRect()
        elif key == QtCore.Qt.Key_Left:
            if state == "Idle":
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{XY_STEP_SIZE:.3f}\n"
                serial.write(cmd)
        elif key == QtCore.Qt.Key_Right:
            if state == "Idle":
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{XY_STEP_SIZE:.3f}\n"
                serial.write(cmd)
        elif key == QtCore.Qt.Key_Up:
            if state == "Idle":
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{XY_STEP_SIZE:.3f}\n"
                serial.write(cmd)
        elif key == QtCore.Qt.Key_Down:
            if state == "Idle":
                cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{XY_STEP_SIZE:.3f}\n"
                serial.write(cmd)
        elif key == QtCore.Qt.Key_PageUp:
            if state == "Idle":
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{Z_STEP_SIZE:.3f}\n"
                serial.write(cmd)
        elif key == QtCore.Qt.Key_PageDown:
            if state == "Idle":
                cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{Z_STEP_SIZE:.3f}\n"
                serial.write(cmd)
        return super().keyPressEvent(event)