import time
import threading
import numpy as np
import json
import paho.mqtt.client as mqtt
import sys
import simplejpeg
import imagezmq
import os
import classes

import tensorflow as tf
from object_detection.utils import config_util
from object_detection.builders import model_builder
MQTT_SERVER="gork.local"
TARGET=sys.argv[1]
PORT=int(sys.argv[2])
IMAGEZMQ='gork.local'


BASE="z:\src"
pipeline_config = os.path.join(BASE,'tensorflow/models/research/object_detection/configs/tf2/ssd_resnet50_v1_fpn_640x640_coco17_tpu-8.config')

# Load pipeline config and build a detection model.

# Since we are working off of a COCO architecture which predicts 90
# class slots by default, we override the `num_classes` field here to be just
# one (for our new tardigrade class).
configs = config_util.get_configs_from_pipeline_file(pipeline_config)
model_config = configs['model']
model_config.ssd.num_classes = classes.num_classes
model_config.ssd.freeze_batchnorm = True
detection_model = model_builder.build(model_config=model_config, is_training=True)
ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(r"z:\src\tardetect\tardigrade-2-1")


def inference(client, image_data=None):
    try:
        t0 = time.time()
        s = image_data.shape
        a = image_data.reshape((s[0], s[1], 3)).astype(np.uint8)
        x = np.expand_dims(a, axis=0)
        input_tensor = tf.convert_to_tensor(x, dtype=tf.float32)
        preprocessed_image, shapes = detection_model.preprocess(input_tensor)
        prediction_dict = detection_model.predict(preprocessed_image, shapes)
        d= detection_model.postprocess(prediction_dict, shapes)
        scores = d['detection_scores'][0].numpy()
        detection_boxes = d['detection_boxes'][0].numpy()
        class_ids = d['detection_classes'][0].numpy()
        t1 = time.time()
        
        results = []
        for i in range(len(scores)):
            score = float(scores[i])
            if score > 0.95:
                db = detection_boxes[i]
                label = classes.id_to_name[int(class_ids[i])+1]
                pt1 = int(db[1]*s[1]), int(db[0]*s[0])
                pt2 = int(db[3]*s[1]), int(db[2]*s[0])
                results.append([score, label, (pt1, pt2)])
        if len(results):
            print(f"publish to",f'{TARGET}/inference')
            print(results)
            client.publish(f'{TARGET}/inference', json.dumps({'size': s, 'results': results}))

    except Exception as e:
            import traceback
            traceback.print_exc()
            print("Exception:", e)

def main():         
    client =  mqtt.Client()
    client.connect(MQTT_SERVER)
    url = f"tcp://{IMAGEZMQ}:{PORT}"
    image_hub = imagezmq.ImageHub(url, REQ_REP=False)
    grid_thread = None
    while True:
        name, jpg_buffer = image_hub.recv_jpg()
        image_data = simplejpeg.decode_jpeg( jpg_buffer, colorspace='RGB')

        if grid_thread is None or not grid_thread.is_alive():
            grid_thread = threading.Thread(target=inference, kwargs={"client": client, "image_data":  image_data.copy()})
            grid_thread.start()
        



if __name__ == "__main__":
    main()
