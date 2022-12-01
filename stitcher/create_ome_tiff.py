import numpy as np
import dask.array as da
import os
import glob
import json
import pandas as pd
import tifffile
import sys
sys.path.append("..")
from microscope_ui.config import FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE, HEIGHT, WIDTH

def main():

    #tif = tifffile.TiffWriter(f"test.ome.tif", )

    d = da.from_zarr(f"/Users/davidek/out/images.zarr")
    # CTZijYX
    print(d.shape)
    for c in range(d.shape[0]):
        print("c=", c)
        for t in range(d.shape[1]):
            print("\tt=", t)
            
            for i in range(d.shape[3]):
                for j in range(d.shape[4]):
                    print("\t\t", i,j)
                    y = i * FOV_Y_PIXELS
                    x = j * FOV_X_PIXELS
                    data = np.array(d[c, t, :, i,j])


                    metadata={
                        'axes': 'ZYXS',
                        #'DimensionOrder': 'TCZYXS',
                        #'TimeIncrement': 0.1,
                        #'TimeIncrementUnit': 's',
                        # 'Interleaved': "true",
                        'SignificantBits': 8,
                        # 'PhysicalSizeX': 1.0,
                        # 'PhysicalSizeXUnit': 'µm',
                        # 'PhysicalSizeY': 1.0,
                        # 'PhysicalSizeYUnit': 'µm',
                        # 'Channel': {'Name': ['Channel 1', 'Channel 2']},

                        # 'TiffData': {
                        #     #'IFD': 0,
                        #     'PlaneCount': data.shape[0],
                        # },
                        'Plane': {
                            #'TheZ': list(range(data.shape[0])),
                            #'PositionX': [x] * data.shape[0       ],
                            #'PositionXUnit': ['µm'] * data.shape[0],
                            #'PositionY': [y] * data.shape[0],
                            #'PositionYUnit': ['µm'] * data.shape[0]
                            'PositionZ': [0]*data.shape[0]
                        },
                    }
                    # print(metadata)
                    options = dict  (
                        photometric='minisblack',
                        tile=(128, 128),
                        compression='jpeg',
                        resolutionunit='CENTIMETER',
                        resolution=(1e4, 1e4))
                    print(data.shape)
                    data = np.expand_dims(data, 3)
                    print(data.shape)
                    tifffile.imwrite("test.tif", data, bigtiff=True, metadata=metadata, **options)
                    return
                    #tif.write(data, metadata=metadata, **options)
main()
