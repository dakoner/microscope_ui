import sys
import json
import numpy as np
import os
import pandas as pd
from PIL import Image
from skimage.registration import phase_cross_correlation
from imreg import translation
import cv2


def main(prefix):
   
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)


    images = {}
    for index, img in r.iterrows():
        image = np.asarray(Image.open(os.path.join(prefix, img.fname)).convert('L'))
        images[index] = image
        #image = cv2.imread(os.path.join(prefix, img.fname))
        #images[index] = image[:720, 280:1280-280 ]

    for index1, img1 in r.iterrows():
        for index2, img2 in r.iterrows():
            # result = imregpoc.imregpoc(images[index1], images[index2])
            # print(index1, index2, result.isSucceed(), result.getParam())
            t0, t1 = translation(images[index1], images[index2]) 
            print(index1, index2, t0, t1)
            #, t0, t1)
            #shift, error, diffphase = phase_cross_correlation(images[index1], images[index2])#
            #print(index1, index2, shift, error, diffphase)


        

if __name__ == '__main__':
    
    prefix = sys.argv[1]   
    main(prefix)