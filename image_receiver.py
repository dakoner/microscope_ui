import os
import imagezmq
import sys
import simplejpeg
import paho.mqtt.client as mqtt
import traceback
IMAGEZMQ='gork.local'
WEBSOCKET_SERVER=sys.argv[1]
PORT=int(sys.argv[2])
MQTT_SERVER="gork.local"

class ImageReader:
    def __init__(self):
        url = f"tcp://{IMAGEZMQ}:{PORT}"
        print("Connect to url", url)
        self.image_hub = imagezmq.ImageHub(url, REQ_REP=False)

        
        self.client =  mqtt.Client("server")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER)
        self.client.loop_start()
        self.take_snapshot = False

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(f"{WEBSOCKET_SERVER}/photo")

    def on_message(self, client, userdata, message):
        # need to fetch images repeatedlyt and just take 1 snapshot using a flag?
        self.take_snapshot = True
        self.filename = message.payload
        print("image write to", message.payload)

        # save image to file

    def run(self):
        while True:
            try:
                name, jpg_buffer = self.image_hub.recv_jpg()
                if self.take_snapshot:
                    fname = os.path.join("movie", self.filename.decode('utf-8').strip())
                    with open(fname, "wb") as f:
                        f.write(jpg_buffer.buffer)
                    print("image wrote to", self.filename)
                    self.take_snapshot = False
            except Exception as e:
                print("Unhandled exception", str(e))
                traceback.print_exc()

def main():
    s = ImageReader()
    s.run()

if __name__ == '__main__':
    main()
