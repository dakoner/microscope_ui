import numpy as np
import time
import sys
import cv2
import imagezmq
import simplejpeg
IMAGEZMQ='microcontroller'
PORT=5000
url = f"tcp://{IMAGEZMQ}:{PORT}"
image_hub = imagezmq.ImageHub(url, REQ_REP=False)

out = None
t0 = time.time()
while True:
    t1 = time.time()
    t0 = t1
    name, jpg_buffer = image_hub.recv_jpg()
    image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='GRAY')
    d = image.sum() / len(image)
    if d> 5000:
        print("non-empty image")
        if out is None:
            out = cv2.VideoWriter('outpy.mkv',cv2.VideoWriter_fourcc(*'XVID'), 10, (image.shape[1], image.shape[0]))
        image = np.repeat(image, repeats=3, axis=2)
        out.write(image)
