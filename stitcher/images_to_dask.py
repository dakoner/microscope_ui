import dask.array as da
import numpy as np
import os
import glob
import json
import pandas as pd
import tifffile
import sys
sys.path.append("..")
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE, HEIGHT, WIDTH

def main():
    #g = glob.glob("movie/*")
    #g.sort()
    #prefix = g[-1]
    prefix="movie/1669690354.4376109"
    #print(prefix)
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    unique_counter = r.counter.unique()
    unique_i = r.i.unique()
    unique_j = r.j.unique()
    unique_k = r.k.unique()
    r.set_index(['counter', 'j', 'k'], inplace=True)

                     #C   T                    Z                                            Y       X
    data = np.zeros((1, len(unique_counter), len(unique_i), len(unique_j), len(unique_k), HEIGHT, WIDTH), dtype=np.uint8)

    for counter in unique_counter:
        print(counter)
        for j in unique_j:
            print("\t", j)
            for k in unique_k:
                d = r.loc[counter, j, k]
                # Z C Y X
                for row in d.itertuples():
                    fname = os.path.join(prefix, row.fname)
                    x = tifffile.imread(fname)
                    data[0, counter,row.i,j,k] = x

    out_fname = f"out/images.zarr"
    data = da.from_array(data)
    data.to_zarr(out_fname)
    return
main()
