import sys
import signal
from PyQt5 import QtGui, QtCore, QtWidgets
import paho.mqtt.client as mqtt
import simplejpeg
import imagezmq
import numpy


XY_STEP_SIZE=5
Z_STEP_SIZE=.005
Z_FEED=.005
XY_FEED=50
TARGET="microscope"
MQTT_SERVER="inspectionscope.local"
#IMAGEZMQ='microscope.local'
IMAGEZMQ='inspectionscope.local'

keys = (QtCore.Qt.Key_0, QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_5, QtCore.Qt.Key_6, QtCore.Qt.Key_7, QtCore.Qt.Key_8, QtCore.Qt.Key_9)
MovementKeys=(QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)

class ImageZMQCameraReader(QtCore.QThread):
    signal = QtCore.pyqtSignal(numpy.ndarray)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:5555"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

    def run(self):         
        name, jpg_buffer = self.image_hub.recv_jpg()
        image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            self.signal.emit(image)#

class Window(QtWidgets.QLabel):

    def __init__(self):
        super(Window, self).__init__()

        self.resize(1600,1200)
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
        self.timer.start(100)

        self.status = None
        self.positions = {}
        self.connected = False


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
                    state = rest[0]
                    results = { 'state': state }
                    for item in rest:
                        if item.startswith("MPos"):
                            m_pos = [float(field) for field in item[5:].split(',')]
                            results['m_pos'] = m_pos
                        elif item.startswith("Pn"):
                            pins = item[3:]
                            results['pins'] = pins
                    self.status = results

            else:
                pass
                # print("Message:", message.payload)
        elif message.topic == f"{TARGET}/command":
            if message.payload != b"?":
                print("Command:", message.payload)

    def mousePressEvent(self, event):
        if self.status is not None:
            # Compute delta from c_pos to middle of window, then scale by pixel size
            s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
            cursor_offset = QtCore.QPointF(event.pos()-s_pos)*.0003
            cmd = "$J=G91 F%.3f X%.3f Y%.3f"% (XY_FEED, cursor_offset.y(), cursor_offset.x())
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
            elif event.key() in keys:
                if event.modifiers() & QtCore.Qt.ControlModifier:
                    if event.key() in self.positions:
                        pos = self.positions[event.key()]
                        cmd = f"G90 F50 X{pos[0]} Y{pos[1]} Z{pos[2]}"
                        self.outstanding += 1
                else:
                    self.positions[event.key()] = self.status['m_pos']
            if cmd:
                self.client.publish(f"{TARGET}/command", cmd)


    def keyReleaseEvent(self, event):
        if event.key() in MovementKeys and not event.isAutoRepeat():
            self.client.publish(f"{TARGET}/cancel")

    def imageTo(self, image):#, this_pose): 
        image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
        if self.status is not None:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            p.drawImage(QtCore.QPoint(), image)

            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            p.setPen(pen)        

            font = QtGui.QFont()
            font.setFamily('Times')
            font.setBold(True)
            font.setPointSize(24)
            p.setFont(font)

            c_pos = self.mapFromGlobal(QtGui.QCursor().pos())
            # Compute delta from c_pos to middle of window, then scale by pixel size
            s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
            self.cursor_offset = QtCore.QPointF(c_pos-s_pos)*.0003
            p.drawText(950, 100, "dX %6.3fmm dY %6.3fmm" % (self.cursor_offset.x(), self.cursor_offset.y()))
            m_pos = self.status['m_pos']
            p.drawText(975, 150, "X%6.3fmm Y%6.3fmm" % (m_pos[0], m_pos[1]))
            p.end()

        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.setPixmap(pixmap)

if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()#FullScreen()

    app.exec_()
