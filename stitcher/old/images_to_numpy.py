import numpy as np
import os
import glob
import pandas as pd
#import tifffile
import json
from PIL import Image
import csv
import shutil
def main():
    # g = glob.glob("photo/*")
    # g.sort()
    # prefix = g[-1]
    prefix = "photo\\test2"

    #d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    data = []
    rows = []
    cols = []
    for index, row in r.iterrows():
        fname = os.path.join(prefix, row.fname)
        #x = tifffile.imread(fname)
        # if not os.path.exists(fname):
        #     shutil.copyfile("photo\\1710633373.1265328\\" + row.fname, fname)
        image = Image.open(fname)
        
        image = image.convert('L')
        #image = image.transpose(Image.FLIP_LEFT_RIGHT)
        image = np.asarray(image)
        image = image.T
        data.append(image)
        rows.append(row.j)
        cols.append(row.k)

    data = np.asarray(data)
    print(data.shape)
    out_fname = f"images.npy"
    np.save(out_fname, data)
    with open('props.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=',',
        
                                quoting=csv.QUOTE_MINIMAL,
                                fieldnames = ["index", "row", "col"]
                                )
        writer.writeheader()
        for index, row in r.iterrows():
            writer.writerow({'index': index, 'row': row['j'], 'col': row['k']})
main()
