import os
import glob
import pandas as pd
import numpy as np
import tifffile
import sys
sys.path.append("..")
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.

def get_data():
    prefix = "c:\\Users\\dek\\Desktop\\acquisition"
    g = glob.glob(os.path.join(prefix, "*.tif"))
    items = [int(item.split(".")[1]) for item in g]
    items.sort()
    fname = os.path.join(prefix, f"frame.{items[0]}.tif")
    data = tifffile.imread(fname)
    s = data.shape
    all = []
    for item in items[:5]:
        fname = os.path.join(prefix, f"frame.{item}.tif")
        data = tifffile.imread(fname)
        # Y X C S
        all.append(data)
    result = np.array(all)
    # T Y X C S
    result = np.expand_dims(result, axis=1)
    # T Z Y X C S
    #result = result.transpose([0, 4, 1  , 2, 3])
    #print(result.shape)
    # T C Z Y X S
    #tifffile.imwrite("c:\\users\\dek\\desktop\\all.tif", result, bigtiff=True, metadata={'axes': 'TCZYX'} )
    return result
# def get_data():
#     o = np.zeros(shape=(t_max, z_max, y_max, x_max, c_max), dtype=np.ubyte)
#     for t in r.acquisition_counter.unique():
#         print(t)
#         # Get all items in time t
#         d = r[r.acquisition_counter == t]


#         # We now have all the CZYX data for a time

#         for row in d.itertuples():
#             fname = row.fname
#             data = tifffile.imread(f"{prefix}/{row.fname}")
#             x0 = row.gx * FOV_X_PIXELS
#             y0 = row.gy * adj_FOV_Y_PIXELS
#             x1 = x0 + WIDTH
#             y1 = y0 + HEIGHT
#             o[t, row.gz, y0:y1, x0:x1] = data
#     return o

if __name__ == '__main__':
    o = get_data()
    # T Z Y X C
    np.save("c:\\Users\\dek\\Desktop\\data.npy", o)
    