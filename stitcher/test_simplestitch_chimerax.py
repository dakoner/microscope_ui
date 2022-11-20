import os
import glob
import pandas as pd
import json
import numpy as np
import tifffile
import sys
sys.path.append("..")
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.

def main():
    g = glob.glob("movie/*")
    g.sort()
    prefix = g[-1]
    print(prefix)
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    r.set_index(['counter', 'i', 'j', 'k'])


    x_max = d['k_dim']*FOV_X_PIXELS+WIDTH
    y_max = d['j_dim']*FOV_Y_PIXELS+HEIGHT
    z_max = d['i_dim']
    for t in r.counter.unique()[:1]:
        print(t)
        # Get all items in time t
        all_t = r[r.counter == t]

        # We now have all the CZYX data for a time    
        for i in range(d['i_dim']):
            print("\t", i, d['i_dim'][:-1])
            all_ti = all_t[all_t.i == i]
            
            o = np.zeros(shape=(3, y_max, x_max), dtype=np.ubyte)
            for row in all_ti.itertuples():
                fname = row.fname
                data = tifffile.imread(os.path.join(prefix, row.fname))
                x0 = row.k * FOV_X_PIXELS
                y0 = row.j * FOV_Y_PIXELS
                x1 = x0 + WIDTH
                y1 = y0 + HEIGHT
                
                for c in range(3):
                    # add this tile's channel-specific data to the full Z-plane
                    o[c, y0:y1, x0:x1] = data[:, :, c]

            for c in range(3):
                #out_fname = f"chimerax\\image_{t}_{c}_{i}.tiff"
                out_fname="chimerax\\" + f"image_{t}_{i}_{c}.tif"
                tifffile.imwrite(out_fname, o[c])
    
if __name__ == '__main__':
    main()