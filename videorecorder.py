import cv2
import imagezmq
import simplejpeg
IMAGEZMQ='inspectionscope.local'

out = cv2.VideoWriter('outpy.mkv',cv2.VideoWriter_fourcc(*'XVID'), 24, (1600, 1200))
url = f"tcp://{IMAGEZMQ}:5556"
image_hub = imagezmq.ImageHub(url, REQ_REP=False)

while True:
    name, jpg_buffer = image_hub.recv_jpg()
    print(name)
    image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
    out.write(image)
