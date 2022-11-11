import pandas as pd
import json
import numpy as np
import tifffile
from config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.

# import zarr
# from ome_zarr.io import parse_url
# from ome_zarr.writer import write_image


# def poke(p, o, data):

#     h0 = p[2]*FOV_Y_PIXELS
#     w0 = p[3]*FOV_X_PIXELS
#     #i = o[p[0], p[1], :, h0:h0+HEIGHT, w0:w0+WIDTH]
#     o[p[0], p[1], :, h0:h0+HEIGHT, w0:w0+WIDTH] = data
# #     T      Z    C  Y              X           
#     return True

# def populate(fname):
#     d = np.load(fname, allow_pickle=True)
#     r = []
#     for f in d.files:
#         r.append(eval(f))
#     max_t = max(r, key=lambda x: x[0])[0]
#     max_z = max(r, key=lambda x: x[1])[1]
#     max_y = max(r, key=lambda x: x[2])[2]
#     max_x = max(r, key=lambda x: x[3])[3]
#     max_c = 3

#     y_size = max_y*FOV_Y_PIXELS+HEIGHT
#     x_size = max_x*FOV_X_PIXELS+WIDTH

#     # TCZYX
#     o = np.zeros(shape=(max_t+1, max_z+1, max_c, y_size, x_size), dtype=np.ubyte)
#     l = list(d.files)

#     for i, f in enumerate(l):
#         print(i, i/len(l))
#         p = eval(f)
#         poke(p, o, d[f])
#     return o

# def write(o):
#     s = o.shape
#     n_time = s[0]
#     n_c = s[2]
#     for i in range(n_time):
#         print(i, n_time)
#         for j in range(n_c):
#             print(" ", j, n_c)
#             fname = f"chimerax/{j}ch_t{i}.tiff"
#             with tifffile.TiffWriter(fname) as tif:
#                 options = dict(
#                     # photometric='rgb',
#                     # tile=(128, 128),
#                     # compression='jpeg',
#                     # resolutionunit='CENTIMETER'
#                 )
#                 tif.write(
#                     o[i, :, j, :, :],
#                     resolution=(1e4 / 1, 1e4 / 1),
#                     metadata= { 'axes': 'ZYX' },
#                     **options)

def main():
    prefix = "movie/1668194778"
    r = pd.read_json(f"{prefix}/tile_config.json", lines=True)
    r.set_index(['acquisition_counter', 'gx', 'gy', 'gz'])
    for t in r.acquisition_counter.unique():
        # Get all items in time t
        d = r[r.acquisition_counter == t]

        x_max = d.gx.max()*FOV_X_PIXELS+WIDTH
        y_max = d.gy.max()*FOV_Y_PIXELS+HEIGHT
        z_max = len(d.gz.unique())


        # We now have all the CZYX data for a time
        # Iterate over all Z planes
        for gz in d.gz.unique():
            d2 = d[d.gz == gz]
            # output: C, Y, X
            o = np.zeros(shape=(3, y_max, x_max), dtype=np.ubyte)
            # all overlapping tiles in this Z plane
            for row in d2.itertuples():
                fname = row.fname
                data = tifffile.imread(row.fname)
                for c in range(3):
                    channel_data = data[:, :, c]
                    x0 = row.gx * FOV_X_PIXELS
                    y0 = row.gy * FOV_Y_PIXELS
                    x1 = x0 + WIDTH
                    y1 = y0 + HEIGHT
                    # add this tile's channel-specific data to the full Z-plane
                    o[c, y0:y1, x0:x1] = channel_data
            for c in range(3):
                out_fname = f"chimerax/image_{t}_{c}_{gz}.tiff"
                with tifffile.TiffWriter(out_fname) as tif:
                    tif.write(o[c])
    
if __name__ == '__main__':
    main()