import cv2
import shapely, shapely.geometry, shapely.strtree
import os
import glob
import pandas as pd
import json
import numpy as np
import tifffile
import sys
import signal
sys.path.append("..")
from microscope_ui.config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS

def addImage(self, pos, image):
    width = image.shape[1]
    height = image.shape[0]


def main():
    g = glob.glob("movie/*")
    g.sort()
    prefix = g[-1]
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    r.set_index(['counter', 'i', 'j', 'k'])

    x_max = d['k_dim']*FOV_X_PIXELS+WIDTH
    y_max = d['j_dim']*FOV_Y_PIXELS+HEIGHT
    z_max = d['i_dim']
    for t in r.counter.unique()[:-1]:
        print("t=",t)
        
        # Get all items in time t
        all_t = r[r.counter == t]

        # We now have all the CZYX data for a time    
        for i in range(d['i_dim']):
            all_ti = all_t[all_t.i == i]
            print("\t", "z=",i)
            
            polys = []
            
            for row in all_ti.itertuples():
                x0 = row.k * FOV_X_PIXELS
                y0 = row.j * FOV_Y_PIXELS
                x1 = x0 + WIDTH
                y1 = y0 + HEIGHT
                b = shapely.geometry.box(x0, y0, x1, y1)
                polys.append(b)
            c = shapely.geometry.MultiPolygon(polys)
            print("Full size", c.bounds)
            # Target array for all images in this T, Z, Y, X, C (shaped as Y, X, C)
            o = np.full((int(c.bounds[3]), int(c.bounds[2]), 3), (0,0,0), dtype=np.ubyte)

            s = shapely.strtree.STRtree([])
            polys = []
            for row in all_ti.itertuples():
                fname = row.fname
                data = tifffile.imread(os.path.join(prefix, row.fname))
                #data_alpha = np.full((data.shape[0], data.shape[1], 1), 255)
                #data = np.concatenate([data, data_alpha], axis=2)
                #print(data.shape)
                x0 = row.k * FOV_X_PIXELS
                y0 = row.j * FOV_Y_PIXELS
                x1 = x0 + WIDTH
                y1 = y0 + HEIGHT
                height = x1-x0
                width = y1-y0
                b = shapely.geometry.box(x1, y0, x0, y1)
                b.row = row
                b.data = data
                results = s.query(b)
                #o2 = np.full((height, width, 4), (0, 0, 0, 255), dtype=np.ubyte)
                #mask = np.full((height, width), 255, dtype=np.ubyte)
                #if len(results) == 0:
                #print(y0, y1, x0, x1)
                o[y0:y1, x0:x1] = data

                # else:
                #     for result in results:
                #         #print("\t\t", result.row, result)
                #         ib = result.intersection(b).bounds
                #         ix0 = int(ib[0])
                #         ix1 = int(ib[2])
                #         iy0 = int(ib[1])
                #         iy1 = int(ib[3])

                #         xs = np.linspace(0, 255, ix1-ix0)
                #         #ys = np.linspace(0, 255, int(ib[3]-ib[1]))
                #         gradient = np.tile(xs, (iy1-iy0,1))
                #         mask[iy0:iy1,ix0:ix1] = gradient
                    
                # print("o2 shape", o2.shape)
                # print(f"box {y0}:{y1}, {x0}:{x1}")
                # print("data shape", data.shape)
                # o2[y0:y1, x0:x1, :3] = data
                # print("mask shape", mask.shape)
                # o2[:, :, 3] = mask
                tifffile.imwrite("movie_out/test.%05d.tif" % t, o)
                #tifffile.imwrite("test2.png", o2)
                #tifffile.imwrite("test3.png", o3)
                #import pdb; pdb.set_trace()
                polys.append(b)
                s = shapely.strtree.STRtree(polys)
            fname = f"stitched/image_t={t},z={i}.tif"
            tifffile.imwrite(
                fname,
                o,
                tile=(32, 32),
                compression='zlib',
                compressionargs={'level': 8},
                metadata={'axes': 'TZYXC'}
                )


main()