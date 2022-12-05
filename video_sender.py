import numpy as np
import imagezmq
import simplejpeg
import cv2
import sys
import serial
import time
import threading
import paho.mqtt.client as mqtt
from config import WIDTH, HEIGHT, FPS, TARGET, MQTT_HOST
from simple_pyspin import Camera

IMAGE_TIMEOUT=0.1
STATUS_TIMEOUT=0.1
port = 5000


class VideoSender:
    
    def __init__(self):
        super().__init__()

    def get_image(self):
        sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)

        cam = Camera()
        cam.Width = 1280
        cam.Height = 720
        cam.init()
        cam.start()
        t0 = time.time()
        counter=0
        while True:
            img = cam.get_array()
            #img = np.ones((720,1280), dtype=np.ubyte)
            
            t1 = time.time()
            if t1 - t0 >= IMAGE_TIMEOUT:
                img = img[..., np.newaxis]
                jpg_buffer = simplejpeg.encode_jpeg(img, quality=100, colorspace='GRAY')
                sender.send_jpg("image", jpg_buffer)
                t0 = t1
            counter += 1

    # def get_image(self):
    #     cap = cv2.VideoCapture('/dev/video0', 0)
    #     port = 5000
    #     cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc('M','J','P','G'))
    #     cap.set(cv2.CAP_PROP_FPS, FPS)
    #     cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    #     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    #     sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)
    #     counter = 0
    #     t0 = time.time()
        
    #     while True:
    #         ret = cap.grab()
    #         if ret:
    #             t1 = time.time()
    #             if t1 - t0 >= IMAGE_TIMEOUT:
    #                 # self.m_pos = 0, 0, 0
    #                 ret, img = cap.retrieve()
    #                 if ret:
    #                     jpg_buffer = simplejpeg.encode_jpeg(img, quality=100, colorspace='BGR')
    #                     sender.send_jpg("", jpg_buffer)
    #                     t0 = t1
    #             counter += 1
        


def main():
    s = VideoSender()
    s.get_image()

if __name__ == "__main__":
    main()
