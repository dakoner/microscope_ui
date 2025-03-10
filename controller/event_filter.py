import time
from PyQt6 import QtCore, QtGui
from config import PIXEL_SCALE, MQTT_HOST, XY_FEED, XY_STEP_SIZE, Z_FEED, Z_STEP_SIZE

class EventFilter(QtCore.QObject):
    def __init__(self, main_window, *args, **kwargs):
        self.main_window = main_window
        super().__init__(*args, **kwargs)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()

            state = self.main_window.state

            if key == QtCore.Qt.Key.Key_C:
                self.main_window.cancel()

            elif key == QtCore.Qt.Key.Key_Q:
                app = QtGui.QApplication.instance()
                app.quit()
            elif key == QtCore.Qt.Key.Key_H:
                self.main_window.cancel()
                self.main_window.home()
            elif key == QtCore.Qt.Key.Key_X:
                self.main_window.trigger()
            elif key == QtCore.Qt.Key.Key_U:
                self.main_window.unlock()
            elif key == QtCore.Qt.Key.Key_E:
                self.main_window.reset()
            # elif key == QtCore.Qt.Key.Key_P:
            #     r = self.main_window.camera.snapshot()
            #     print(r)
            elif key == QtCore.Qt.Key.Key_S:
                self.main_window.cancel()
                self.main_window.tile_graphics_view.stopAcquisition()
            elif key == QtCore.Qt.Key.Key_P:
                fname = f"image_{int(time.time())}.png"
                time.sleep(1)
                self.main_window.curr_image.save(fname)
                print("Saved", fname)
            elif key == QtCore.Qt.Key.Key_R:
                print("Reset")
                self.main_window.tile_graphics_view.reset()
                self.main_window.tile_graphics_view.addCurrentRect()
                # self.main_window.serial.reset()
            elif key == QtCore.Qt.Key.Key_Left:
                if state == "Idle":
                    d = XY_STEP_SIZE
                    if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        d *= 10
                    elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                        d /= 10
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} X-{d:.3f}\n"

                    self.main_window.serial.write(cmd)
            elif key == QtCore.Qt.Key.Key_Right:
                if state == "Idle":
                    d = XY_STEP_SIZE
                    if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        d *= 10
                    elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                        d /= 10
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} X{d:.3f}\n"
                    self.main_window.serial.write(cmd)
            elif key == QtCore.Qt.Key.Key_Up:
                if state == "Idle":
                    d = XY_STEP_SIZE
                    if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        d *= 10
                    elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                        d /= 10
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y-{d:.3f}\n"
                    self.main_window.serial.write(cmd)
            elif key == QtCore.Qt.Key.Key_Down:
                if state == "Idle":
                    d = XY_STEP_SIZE
                    if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        d *= 10
                    elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                        d /= 10
                    cmd = f"$J=G91 G21 F{XY_FEED:.3f} Y{d:.3f}\n"
                    self.main_window.serial.write(cmd)
            elif key == QtCore.Qt.Key.Key_PageUp:
                if state == "Idle":
                    d = Z_STEP_SIZE
                    if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        d *= 10
                    elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                        d /= 10
                    cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z-{d:.3f}\n"
                    self.main_window.serial.write(cmd)
            elif key == QtCore.Qt.Key.Key_PageDown:
                if state == "Idle":
                    d = Z_STEP_SIZE
                    if event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier:
                        d *= 10
                    elif event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                        d /= 10
                    cmd = f"$J=G91 G21 F{Z_FEED:.3f} Z{d:.3f}\n"
                    self.main_window.serial.write(cmd)
            # return super().keyPressEvent(event)event

        # elif (
        #     not isinstance(event, QtGui.QPaintEvent)
        #     and not event.type() == QtCore.QEvent.UpdateRequest
        #     and not event.type() == QtCore.QEvent.LayoutRequest
        #     and not event.type() == QtCore.QEvent.ActivationChange
        #     and not event.type() == QtCore.QEvent.WindowActivate
        #     and not event.type() == QtCore.QEvent.WindowDeactivate
        #     and not event.type() == QtCore.QEvent.ShortcutOverride
        #     and not event.type() == QtCore.QEvent.Enter
        #     and not event.type() == QtCore.QEvent.HoverEnter
        #     and not event.type() == QtCore.QEvent.Move
        #     and not event.type() == QtCore.QEvent.ChildPolished
        #     and not event.type() == QtCore.QEvent.Resize
        #     and not event.type() == QtCore.QEvent.PolishRequest
        #     and not event.type() == QtCore.QEvent.ShowToParent
        #     and not event.type() == QtCore.QEvent.PlatformSurface
        # ):
        #     pass
            # print(obj, event.type(), event.Type())
        return super(EventFilter, self).eventFilter(obj, event)
