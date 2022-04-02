import cv2
import time
import sys
import signal
from PIL import Image, ImageDraw, ImageFont
from PyQt5 import QtGui, QtCore, QtWidgets
from six import BytesIO
import paho.mqtt.client as mqtt
import simplejpeg
import imagezmq
import numpy as np
import time

import tensorflow as tf
from object_detection.utils import config_util
# from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

pcutoff=0.5
pixel_to_mm = 0.0003
TARGET="inspectionscope"
MQTT_SERVER="gork.local"
IMAGEZMQ='gork.local'
PORT=5556

keys = (QtCore.Qt.Key_0, QtCore.Qt.Key_1, QtCore.Qt.Key_2, QtCore.Qt.Key_3, QtCore.Qt.Key_4, QtCore.Qt.Key_5, QtCore.Qt.Key_6, QtCore.Qt.Key_7, QtCore.Qt.Key_8, QtCore.Qt.Key_9)
MovementKeys=(QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown)
colormap = [QtCore.Qt.red, QtCore.Qt.green, QtCore.Qt.blue, QtCore.Qt.yellow, QtCore.Qt.magenta, QtCore.Qt.black]


tardigrade_class_id = 1
num_classes = 1
category_index = {tardigrade_class_id: {'id': tardigrade_class_id, 'name': 'tardigrade'}}
num_classes = 1
pipeline_config = r'z:\src\tensorflow\models\research\object_detection\configs\tf2\ssd_resnet50_v1_fpn_640x640_coco17_tpu-8.config'

# Load pipeline config and build a detection model.
#
# Since we are working off of a COCO architecture which predicts 90
# class slots by default, we override the `num_classes` field here to be just
# one (for our new tardigrade class).
configs = config_util.get_configs_from_pipeline_file(pipeline_config)
model_config = configs['model']
model_config.ssd.num_classes = num_classes
model_config.ssd.freeze_batchnorm = True
detection_model = model_builder.build(model_config=model_config, is_training=True)
ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(r"z:\src\tardetect\tardigrade-1-1")

counter = 0


fontScale = 1
color = (255, 0, 0)
thickness = 2
font = cv2.FONT_HERSHEY_SIMPLEX

class TFDetection(QtCore.QThread):
    predictSignal = QtCore.pyqtSignal(float, QtCore.QRect)

    def __init__(self, image):
        super().__init__()
        self.image = image

    def run(self):
        try:
            s = self.image.shape
            a= self.image.reshape((s[0], s[1], 3)).astype(np.uint8)
            x = np.expand_dims(a, axis=0)
            input_tensor = tf.convert_to_tensor(x, dtype=tf.float32)
            preprocessed_image, shapes = detection_model.preprocess(input_tensor)
            prediction_dict = detection_model.predict(preprocessed_image, shapes)
            d= detection_model.postprocess(prediction_dict, shapes)
            
            score = d['detection_scores'][0].numpy()[0]
            global counter
            counter += 1
            db = d['detection_boxes'][0].numpy()[0]
            pt1 = int(db[1]*s[1]), int(db[0]*s[0])
            pt2 =  int(db[3]*s[1]), int(db[2]*s[0])
            r = QtCore.QRect(QtCore.QPoint(*pt1), QtCore.QPoint(*pt2))
            self.predictSignal.emit(score, r)
        except Exception as e:
            print("Exception:", e)

class ImageZMQCameraReader(QtCore.QThread):
    imageSignal = QtCore.pyqtSignal(np.ndarray)
    predictSignal = QtCore.pyqtSignal(float, QtCore.QRect)
    def __init__(self):
        super(ImageZMQCameraReader, self).__init__()
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)
        self.tf_detector = None
    def run(self):         
        name, jpg_buffer = self.image_hub.recv_jpg()
        image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
        t0 = time.time()

        while True:
            name, jpg_buffer = self.image_hub.recv_jpg()
            image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
            t1 = time.time()
            if t1 - t0 > 0.25:
                if self.tf_detector and not self.tf_detector.isFinished():
                    print("previous detector not finished!")
                else:
                    self.tf_detector = TFDetection(image_data.copy())
                    self.tf_detector.predictSignal.connect(self.predict)
                    self.tf_detector.start()
                t0 = time.time()

            self.imageSignal.emit(image_data)

    def predict(self, score, box):
        self.predictSignal.emit(score, box)
        
class Window(QtWidgets.QLabel):

    def __init__(self):
        super(Window, self).__init__()

        #self.resize(640,480)
        self.camera = ImageZMQCameraReader()
        self.camera.start()
        self.camera.imageSignal.connect(self.imageTo)
        self.camera.predictSignal.connect(self.predictDraw)


        self.client =  mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)
        self.client.loop_start()
        self.outstanding = 0

        self.positions = {}
        self.connected = False

        self.m_pos = None
        self.w_pos = None

        self.time = None
        self.tracking = False
        self.state = "Unknown"

        self.prediction_score = None
        self.prediction_box = None
    
    def predictDraw(self, score, box):
        self.prediction_score = score
        self.prediction_box = box

    def on_message(self, client, userdata, message):
        if message.topic == f"{TARGET}/m_pos":
            self.m_pos = eval(message.payload)

    def on_connect(self, client, userdata, flags, rc):
        print("connected")
        self.connected = True
        self.client.subscribe(f"{TARGET}/output")
        self.client.subscribe(f"{TARGET}/command")
        self.client.subscribe(f"{TARGET}/status")
        self.client.subscribe(f"{TARGET}/m_pos")


    def on_disconnect(self, client, userdata, flags):
        print("disconnected")
        self.connected = False
        #self.timer.stop()


    def mousePressEvent(self, event):
        # Compute delta from c_pos to middle of window, then scale by pixel size
        s_pos = QtCore.QPoint(self.size().width()/2, self.size().height()/2)
        cursor_offset = QtCore.QPointF(event.pos()-s_pos)*pixel_to_mm
        cmd = "$J=G91 G0  X%.3f Y%.3f F%.3f"% (cursor_offset.y(), cursor_offset.x(), XY_FEED)
        self.client.publish(f"{TARGET}/command", cmd)

    def imageTo(self, image): 
        image = QtGui.QImage(image, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888)
        #(self.m_pos)
        
        if self.m_pos is not None:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            #p.drawImage(QtCore.QPoint(), image)

            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            p.setPen(pen)        

            font = QtGui.QFont()
            font.setFamily('Times')
            font.setBold(True)
            font.setPointSize(24)
            p.setFont(font)

            p.drawText(0, 50, "X%8.3fmm" % self.m_pos[0])
            p.drawText(0, 100, "Y%8.3fmm" % self.m_pos[1])
            p.drawText(0, 150, "Z%8.3fmm" % self.m_pos[2])
            p.end()

        if self.prediction_score and self.prediction_score > 0.35:
            p = QtGui.QPainter()
        
            p.begin(image)
            p.setCompositionMode( QtGui.QPainter.CompositionMode_SourceOver )
            p.setRenderHints( QtGui.QPainter.HighQualityAntialiasing )

            pen = QtGui.QPen(QtCore.Qt.red)
            pen.setWidth(2)
            p.setPen(pen)  
            p.drawRect(self.prediction_box)
            
            pen = QtGui.QPen(QtCore.Qt.green)
            pen.setWidth(2)
            p.setPen(pen)  
            p.drawText(self.prediction_box.bottomRight(), "%5.2f" % self.prediction_score)
            
            image_center = QtCore.QPoint(image.width()/2, image.height()/2)
            dt = self.prediction_box.center() - image_center
            print(image_center, self.prediction_box.center(), dt)

            p.drawEllipse(QtCore.QRect(image_center - QtCore.QPoint(2,2), image_center + QtCore.QPoint(2,2)))
            p.drawLine(image_center, self.prediction_box.center())

            p.end()

        pixmap = QtGui.QPixmap.fromImage(image)#.scaled(QtWidgets.QApplication.instance().primaryScreen().size(), QtCore.Qt.KeepAspectRatio)
        self.resize(pixmap.size().width(), pixmap.size().height())
        self.setPixmap(pixmap)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.show()#FullScreen()

    app.exec_()

