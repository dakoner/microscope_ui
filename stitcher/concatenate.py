import PIL
import signal
import dask.array as da

from numcodecs import Blosc
import pathlib
from lxml import etree as ET
import sys
import tifffile

sys.path.insert(0, "controller")
import numpy as np
import math
import time
import shapely, shapely.geometry, shapely.strtree
from tile_configuration import TileConfiguration
from PIL import Image
import sys
import concurrent.futures
from util import get_image_data, get_image_dimensions, CHUNK_SIZE



def do(x, y, fname):
    return x, y, get_image_data(fname)

def round_up(val):
    x = int(val / CHUNK_SIZE)
    return CHUNK_SIZE * (x + 1)


def main(prefix):
    tc = TileConfiguration()
    tc.load(f"{prefix}/TileConfiguration.txt")
    tc.move_to_origin()

    polys = []
    box_to_fname = {}
    for image in tc.images:
        filename = pathlib.Path(prefix) / image.filename
        width, height = get_image_dimensions(filename)

        b = shapely.geometry.box(
            int(image.x),
            int(image.y),
            int(image.x) + width,
            int(image.y) + height,
        )
        box_to_fname[b] = filename
        polys.append(b)

    c = shapely.geometry.GeometryCollection(polys)
    # iterate over chunks from the full size image
    # find all the intersecting polys
    # composite the chunk from the intersecting polys
    bounds = round_up(c.bounds[2]), round_up(c.bounds[3])
    d = da.zeros((bounds[0], bounds[1], 3), dtype=np.uint8)


    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for x in range(0, int(c.bounds[2]), CHUNK_SIZE):
            for y in range(0, int(c.bounds[3]), CHUNK_SIZE):
                fname = f"out\\temp.ome.{x},{y}.tif"
                futures.append(executor.submit(do, x, y, fname))

        for future in concurrent.futures.as_completed(futures):
            x, y, results = future.result()
            print("Finished", x, y)
            d[x : x + CHUNK_SIZE, y : y + CHUNK_SIZE] = results
    fname = "test.tif"
    tifffile.imwrite(
            fname,
            d,
            #bigtiff=True,
            #imagej=True,
            resolution=(833, 833),
            metadata={"unit": "mm", "axes": "CYX"},
        )
          
    #da.moveaxis(d, 2, 0).to_zarr("temp.zarr", compressor=Blosc(cname='zstd', clevel=3))

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main(sys.argv[1])
    #main("C:\\Users\\davidek\\Desktop\\1732488657.752864")
    # main("controller\\photo\\1732319758.459453")
