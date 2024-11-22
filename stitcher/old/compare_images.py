import numpy as np
import cv2
import json
import os
import pandas as pd
import glob
import tifffile
import concurrent.futures


def compare(img1, fname):
    img2 = tifffile.imread(fname).astype(np.int64)
    h, w = img1.shape
    diff = img1 - img2
    err = np.sum(diff**2)
    mse = err/(float(h*w))
    return mse
 

def main(comparison_image, prefix):
   
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)


    with open("results.json", "w") as f:
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ProcessPoolExecutor(max_workers=32) as executor:
            future_to_fname = {executor.submit(compare, comparison_image, os.path.join(prefix, row.fname)): row.fname for row in r.itertuples()}
            for future in concurrent.futures.as_completed(future_to_fname):
                fname = future_to_fname[future]
                try:
                    sim = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (fname, exc))
                else:
                    print('%r is %f from comparison' % (fname, sim))
                    f.write(json.dumps({'fname': fname, 'similarity': sim}))
                    f.write("\n")
                    f.flush()


if __name__ == '__main__':
    black = tifffile.imread("black.tif").astype(np.int64)
    g = glob.glob("movie/*")
    g.sort()
    prefix = g[-1]
    print(prefix)
    
    main(black, prefix)