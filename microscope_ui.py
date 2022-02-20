import time
import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import paho.mqtt.client as mqtt
import simplejpeg
import imagezmq
import numpy as np
from dlclive import DLCLive

pcutoff=0.5
pixel_to_mm = 0.0003
XY_STEP_SIZE=500
Z_STEP_SIZE=.01
Z_FEED=500
XY_FEED=1000
TARGET="microscope"
MQTT_SERVER="inspectionscope.local"
#IMAGEZMQ='microscope.local'
IMAGEZMQ='inspectionscope.local'

keys = (QtCore.Qt.Key_0, QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_5, QtCore.Qt.Key_6, QtCore.Qt.Key_7, QtCore.Qt.Key_8, QtCore.Qt.Key_9)
MovementKeys=(QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)
colormap = [QtCore.Qt.red, QtCore.Qt.green, QtCore.Qt.blue, QtCore.Qt.yellow, QtCore.Qt.magenta, QtCore.Qt.black]

class ImageZMQCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:5555"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)


        # self.live = DLCLive(
        #     model_path = r"C:\Users\dek\Desktop\tarditrack2-dek-2022-02-18\exported-models\DLC_tarditrack2_resnet_50_iteration-0_shuffle-1",
        #     tf_config=None,
        #     resize=0.5,
        #     cropping=None,
        #     dynamic=(False, 0.5, 10),
        #     display=False,
        #     pcutoff=0.5,
        #     display_radius=3,
        #     display_cmap='bmy',
        # )

    def run(self):         
        name, jpg_buffer = self.image_hub.recv_jpg()
        image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
        #poses = self.live.init_inference(image)

        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            #poses = self.live.get_pose(image)
            #self.signal.emit(image, poses)
            self.signal.emit(image, np.zeros((5,3)))

class Window(QtWidgets.QLabel):

    def __init__(self):
        super(Window, self).__init__()

        #self.resize(640,480)
        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.signal.connect(self.imageTo)

        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)
        self.client.loop_start()
        self.outstanding = 0

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_tick)
        self.timer.start(500)

        self.positions = {}
        self.connected = False

        self.m_pos = None
        self.w_pos = None

        self.time = None
        self.tracking = False
        self.state = "Unknown"

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True
        self.client.subscribe(f"{TARGET}/output")
        self.client.subscribe(f"{TARGET}/command")


    def timer_tick(self):
        if self.connected:
            self.client.publish(f"{TARGET}/command", '?')

    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
        self.timer.stop()

    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/output":
            if message.payload == b"ok":
                self.outstanding -= 1
            elif message.payload.startswith(b'<'):                          
                status = message.payload.decode('utf8')
                if status.startswith("<") and status.endswith(">"):
                    rest = status[1:-3].split('|')
                    self.state = rest[0]
                    for item in rest:
                        if item.startswith("MPos"):
                            self.m_pos = [float(field) for field in item[5:].split(',')]
                            print(self.m_pos)
                        elif item.startswith("WCO"):
                            self.w_pos = [float(field) for field in item[4:].split(',')]

            else:
                pass
                # print("Message:", message.payload)
        elif message.topic == f"{TARGET}/command":
            if message.payload != b"?":
                print("Command:", message.payload)

    def mousePressEvent(self, event):
        # Compute delta from c_pos to middle of window, then scale by pixel size
        s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
        cursor_offset = QtCore.QPointF(event.pos()-s_pos)*pixel_to_mm
        cmd = "$J=G91  X%.3f Y%.3f F%.3f"% (cursor_offset.y(), cursor_offset.x(), XY_FEED)
        self.client.publish(f"{TARGET}/command", cmd)

    def keyPressEvent(self, event):
        if not event.isAutoRepeat():
            cmd = None
            if event.key() == QtCore.Qt.Key_PageUp:
                cmd = f"$J=G91 F{Z_FEED}"
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    cmd += " Z-%f" % (Z_STEP_SIZE*10)
                else:
                    cmd += " Z-%f" % Z_STEP_SIZE
                self.outstanding += 1
            elif event.key() == QtCore.Qt.Key_PageDown:
                cmd = f"$J=G91 F{Z_FEED}"
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    cmd += f" Z%f" % (Z_STEP_SIZE*10)
                else:
                    cmd += f" Z%f" % Z_STEP_SIZE
                self.outstanding += 1
            elif event.key() == QtCore.Qt.Key_Left:
                cmd = f"$J=G91 F{XY_FEED}"
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    cmd += " Y-%f" % (XY_STEP_SIZE*10)
                else:
                    cmd += " Y-%f" % XY_STEP_SIZE

                self.outstanding += 1
            elif event.key() == QtCore.Qt.Key_Right:
                cmd = f"$J=G91 F{XY_FEED}"
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    cmd += " Y%f" % (XY_STEP_SIZE*10)
                else:
                    cmd += " Y%f" % XY_STEP_SIZE
                self.outstanding += 1
            elif event.key() == QtCore.Qt.Key_Down:
                cmd = f"$J=G91 F{XY_FEED}"
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    cmd += " X%f" % (XY_STEP_SIZE*10)
                else:
                    cmd += " X%f" % XY_STEP_SIZE
                self.outstanding += 1
            elif event.key() == QtCore.Qt.Key_Up:
                cmd = f"$J=G91 F{XY_FEED}"
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    cmd += " X-%f" % (XY_STEP_SIZE*10)
                else:
                    cmd += " X-%f" % XY_STEP_SIZE
                self.outstanding += 1
            elif event.key() == QtCore.Qt.Key_X:
                QtWidgets.qApp.quit()
            elif event.key() == QtCore.Qt.Key_S:
                self.serpentine()
            elif event.key() == QtCore.Qt.Key_R:
                self.reset()
            elif event.key() == QtCore.Qt.Key_T:
                self.tracking = not self.tracking
            elif event.key() == QtCore.Qt.Key_C:
                self.cancel()
            elif event.key() in keys:
                if event.modifiers() & QtCore.Qt.ControlModifier:
                    if event.key() in self.positions:
                        pos = self.positions[event.key()]
                        dx = pos[0] - self.m_pos[0]
                        dy = pos[1] - self.m_pos[1]
                        cmd = f"$J=G91 X{dx} Y{dy} F{XY_FEED}"
                        print("goto", pos)
                        self.outstanding += 1
                else:
                    if self.m_pos is not None:
                        print("save", self.m_pos)
                        self.positions[event.key()] = self.m_pos
            if cmd:
                self.client.publish(f"{TARGET}/command", cmd)

    def reset(self):
        #self.client.publish(f"{TARGET}/reset", "")
        self.client.publish(f"{TARGET}/command", "G10 L20 P0 X0 Y0 Z0")

    def cancel(self):
        self.client.publish(f"{TARGET}/cancel")

    def serpentine(self):
        if QtCore.Qt.Key_0 in self.positions and QtCore.Qt.Key_1 in self.positions:
            # create a serpentine path, moving 1/2 FOV at a time, from 0 to 1
            pos0 = np.array(self.positions[QtCore.Qt.Key_0])
            pos1 = np.array(self.positions[QtCore.Qt.Key_1])
            half_fov = 0.1
            xs = np.arange(pos0[0], pos1[0], half_fov)
            ys = np.arange(pos0[1], pos1[1], half_fov)
            xx, yy = np.meshgrid(xs, ys)
            self.s_grid = np.vstack([xx.ravel(), yy.ravel()]).T
            
            self.s_index = 0
            cmd = "$J=G90 F%.3f X%.3f Y%.3f" % (XY_FEED, self.s_grid[self.s_index][0], self.s_grid[self.s_index][1])
            self.client.publish(f"{TARGET}/command", cmd)
            self.s_timer = QtCore.QTimer()
            self.s_timer.timeout.connect(self.serpentine_tick)
            self.s_timer.start(100)

    def serpentine_tick(self):
        if self.state != 'Idle':
            return
        cmd = "$J=G90 F%.3f X%.3f Y%.3f" % (XY_FEED, self.s_grid[self.s_index][0], self.s_grid[self.s_index][1])
        print(cmd)
        self.client.publish(f"{TARGET}/command", cmd)
        self.s_index += 1
        if self.s_index == len(self.s_grid):
            self.s_timer.stop()

    def keyReleaseEvent(self, event):
        if event.key() in MovementKeys and not event.isAutoRepeat():
            self.client.publish(f"{TARGET}/cancel")

    def imageTo(self, image, this_pose): 
        image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
        
        if self.m_pos is not None:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            #p.drawImage(QtCore.QPoint(), image)

            # pen = QtGui.QPen(QtCore.Qt.red)
            # pen.setWidth(2)
            # p.setPen(pen)        

            # font = QtGui.QFont()
            # font.setFamily('Times')
            # font.setBold(True)
            # font.setPointSize(24)
            # p.setFont(font)

            # c_pos = self.mapFromGlobal(QtGui.QCursor().pos())
            # # Compute delta from c_pos to middle of window, then scale by pixel size
            # s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
            # self.cursor_offset = QtCore.QPointF(c_pos-s_pos)*pixel_per_mm
            # p.drawText(950, 100, "dX %6.3fmm dY %6.3fmm" % (self.cursor_offset.x(), self.cursor_offset.y()))
            # p.drawText(975, 150, "X%6.3fmm Y%6.3fmm" % (self.m_pos[0], self.m_pos[1]))

            if self.tracking and this_pose[1,2] > pcutoff:
                x = int(this_pose[1, 0])
                y = int(this_pose[1, 1])
                pos = QtCore.QPoint(x, y)
                s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
                offset = QtCore.QPointF(pos-s_pos)*pixel_to_mm
                cmd = "$J=G91 F%.3f X%.3f Y%.3f"% (XY_FEED, offset.y(), offset.x())
                t = time.time()
                if self.time is None or t - self.time > 1.5:
                    self.client.publish(f"{TARGET}/command", cmd)
                    self.time = t

            for j in range(this_pose.shape[0]):
                if this_pose[j, 2] > pcutoff:
                    x = int(this_pose[j, 0])
                    y = int(this_pose[j, 1])
                    
                    p.setBrush(colormap[j])
                    p.setPen(QtGui.QPen(colormap[j]))   
                    p.drawEllipse(x, y, 5, 5 )
            p.end()

        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.resize(pixmap.size().width(), pixmap.size().height())
        self.setPixmap(pixmap)

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()#FullScreen()

    app.exec_()
