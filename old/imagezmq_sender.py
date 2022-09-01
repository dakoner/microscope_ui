import time
import sys
import imagezmq
import simplejpeg
import numpy as np

HOST='raspberrypi'
#port = 5555

#width = 3264;height = 2448
#width = 640; height = 480
#width=640; height=480
#width=1280;height=720
width=800;height=600

if __name__ == '__main__':
    import cv2
    cap = cv2.VideoCapture(int(sys.argv[1]))
    port = int(sys.argv[2])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)

    counter = 0
    t0 = time.time()
    while True:
        ret, img = cap.read()
        if ret:
            t1 = time.time()
            if t1 - t0 >= 0.1:
            #if counter % 5 == 0:
                jpg_buffer = simplejpeg.encode_jpeg(img, quality=100, colorspace='BGR')
                sender.send_jpg(HOST, jpg_buffer)
                t0 = t1
        counter += 1
