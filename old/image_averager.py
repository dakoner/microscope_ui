import numpy as np
import os
import imagezmq
import sys
import simplejpeg
import paho.mqtt.client as mqtt
import traceback
IMAGEZMQ='dekscope.local'
WEBSOCKET_SERVER=sys.argv[1]
PORT=int(sys.argv[2])
MQTT_SERVER="dekscope.local"

# 13 pixels = 0.01mm
# so 1mm = 1300
class ImageReader:
    def __init__(self):
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

        
        self.client =  mqtt.Client("server")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)
        

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(f"{WEBSOCKET_SERVER}/photo")

    def on_message(self, client, userdata, message):
        try:
            snapshots = []
            for i in range(1000):
                print("collecting", i)
                name, jpg_buffer = self.image_hub.recv_jpg()
                image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')
                snapshots.append(image_data)

            n = np.average(snapshots, axis=0)
            n = n.astype(np.uint8)
            jpg_buffer = simplejpeg.encode_jpeg(n, quality=100, colorspace='BGR')
            fname = os.path.join("movie", message.payload.decode('utf-8').strip())
            with open(fname, "wb") as f:
                f.write(jpg_buffer)
            print("wrote", fname)
        except:
            traceback.print_exc()

def main():
    s = ImageReader()
    s.client.loop_forever()

if __name__ == '__main__':
    main()
