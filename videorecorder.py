import cv2
import imagezmq
import simplejpeg
IMAGEZMQ='gork'
PORT=5555
url = f"tcp://{IMAGEZMQ}:{PORT}"
image_hub = imagezmq.ImageHub(url, REQ_REP=False)

out = None
i = 0
while True:
    name, jpg_buffer = image_hub.recv_jpg()
    image= simplejpeg.decode_jpeg( jpg_buffer, colorspace='BGR')
    if out is None:
        out = cv2.VideoWriter('outpy.mkv',cv2.VideoWriter_fourcc(*'XVID'), 24, (image.shape[1], image.shape[0]))
    if i % 20 == 0:
        out.write(image)
    i += 1
