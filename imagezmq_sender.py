import time
import sys
import imagezmq
import simplejpeg
import numpy as np

HOST='gork.local'
#port = 5555

# if __name__ == '__main__':
#    from simple_pyspin import Camera
#    cam = Camera()
#    cam.init()
#    sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)
#    cam.start()
#    while True:
#        img = cam.get_array()
#        # Convert to 3 dimensions
#        img = img[..., np.newaxis]
#        # Repeat inner element to turn 8-bit grayscale into 8-bit RGB.
       
#        img = np.repeat(img, repeats=3, axis=2)
#        jpg_buffer = simplejpeg.encode_jpeg(img, quality=55, colorspace='RGB')
#        sender.send_jpg("inspectionscope", jpg_buffer)


if __name__ == '__main__':
    import cv2
    cap = cv2.VideoCapture(int(sys.argv[1]))
    port = int(sys.argv[2])
    #width = 3264;height = 2448
    #width = 640; height = 480
    #width=640; height=480
    width=1600;height=1200
    #width=1280;height=720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    sender = imagezmq.ImageSender("tcp://*:{}".format(port), REQ_REP=False)

    counter = 0
    t0 = time.time()
    while True:
        ret, img = cap.read()
        if ret:
            t1 = time.time()
            if t1 - t0 >= 0.05:
            #if counter % 5 == 0:
                #b, g, r = cv2.split(img)
                #result = g
                #result = (r+b)/(r-b+0.0001)*256
                #print(result)
                #img = cv2.merge([result, result, result]).astype(np.uint8)
                jpg_buffer = simplejpeg.encode_jpeg(img, quality=100, colorspace='BGR')
                sender.send_jpg(HOST, jpg_buffer)
                t0 = t1
        counter += 1
