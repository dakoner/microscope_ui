import json
import imagezmq
import simplejpeg
import cv2
import sys
import serial
import time
import threading
import paho.mqtt.client as mqtt
from config import WIDTH, HEIGHT

IMAGE_TIMEOUT=0.01


class VideoSender:
    
    def __init__(self):
        super().__init__()

    def get_image(self):
        cap = cv2.VideoCapture('/dev/video0', 0)
        cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc('M','J','P','G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, 30)

        port = 5000
        sender = imagezmq.ImageSender('tcp://*:{}'.format(port), REQ_REP=False)
        counter = 0
        t0 = time.time()
        
        while True:
            ret = cap.grab()
            if ret:
                t1 = time.time()
                if t1 - t0 >= IMAGE_TIMEOUT:
                    ret, img = cap.retrieve()
                    if ret:
                        jpg_buffer = simplejpeg.encode_jpeg(img, quality=100, colorspace='BGR')
                        d = json.dumps({'m_pos': [0,0,0], 'state': 'None', 'time': str(t1)})
                        sender.send_jpg(d, jpg_buffer)
                        t0 = t1
                    
                counter += 1
           
        
def main():
    s = VideoSender()
    s.get_image()

if __name__ == '__main__':
    main()
