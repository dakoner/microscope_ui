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
    g = glob.glob("movie/*")
    g.sort()
    prefix = g[-1]
    #prefix="movie/1669690354.4376109"
    #print(prefix)
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    unique_counter = r.counter.unique()[:-1]
    unique_i = r.i.unique()
    unique_j = r.j.unique()
    unique_k = r.k.unique()
    r.set_index(['counter', 'j', 'k'], inplace=True)

    tif = tifffile.TiffWriter(f"test.ome.tif", bigtiff=True, ome=True)

    for counter in unique_counter:
        for j in unique_j:
            for k in unique_k:
                d = r.loc[counter, j, k]
                # Z C Y X
                
                for row in d.itertuples():
                    fname = os.path.join(prefix, row.fname)
                    x = tifffile.imread(fname)
                    

                    # TODO(dek): use the values from scan_config, not config.py
                    x0 = k * FOV_X_PIXELS
                    y0 = j * FOV_Y_PIXELS

                    metadata={
                        'axes': 'ZTCYX',
                        'Channel': { 'Name': 'foo'},
                        'Time'
                        'Interleaved': "true",
                        'SignificantBits': 8,
                        'PhysicalSizeX': 1.0,
                        'PhysicalSizeXUnit': 'µm',
                        'PhysicalSizeY': 1.0,
                        'PhysicalSizeYUnit': 'µm',
                        'TiffData': {
                            'IFD': 0,
                            'PlaneCount': 1,
                        },
                        'Plane': {
                            'TheZ': row.i,
                            'PositionX': x0,
                            'PositionXUnit': 'µm',
                            'PositionY': y0,
                            'PositionYUnit': 'µm'
                        }
                    }
                    options = dict(
                        photometric='minisblack',
                        tile=(128, 128),
                        compression='jpeg',
                        resolutionunit='CENTIMETER'
                    )
                    x = np.expand_dims(x, axis=0)
                    x = np.expand_dims(x, axis=0)
                    x = np.expand_dims(x, axis=2)
                    tif.write(x, metadata=metadata, **options)
    return
main()
