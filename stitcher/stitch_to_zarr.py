import cv2
import dask.array
import tqdm
import PIL
import signal
from numcodecs import Blosc
import pathlib
from lxml import etree as ET
import sys
import tifffile
import zarr

sys.path.insert(0, "controller")
import numpy as np
import math
import time
import shapely, shapely.geometry, shapely.strtree
from tile_configuration import (
    TileConfiguration,
    tile_config_to_tileconfiguration,
    tile_config_to_shapely,
)
from PIL import Image
import sys
import concurrent.futures
from util import get_image_data, get_image_dimensions, CHUNK_SIZE


def fn(prefix, image):
    try:
        filename = pathlib.Path(prefix) / image.filename
        x = int(image.x)
        y = int(image.y)
        img = get_image_data(filename).swapaxes(0,1)

        width = img.shape[0]
        height = img.shape[1]
    except Exception as exc:
        print('%r generated an exception: %s' % (image, exc))
        return None
    return filename, img, x, y, width, height

def main(prefix):
    tc = TileConfiguration()
    fname = prefix / "TileConfiguration.txt"
    if not fname.exists():
        tile_config_to_tileconfiguration(prefix)
    tc.load(fname)
    tc.move_to_origin()
    c = tile_config_to_shapely(prefix, tc)
    print(c.bounds)
    z = zarr.open(
        "test.zarr",
        mode="w",
        shape=(c.bounds[2], c.bounds[3], 3),
        chunks=(CHUNK_SIZE, CHUNK_SIZE, 3),
        dtype=np.uint16,
    )
    counter = zarr.open(
        "counter.zarr",
        mode="w",
        shape=(c.bounds[2], c.bounds[3], 3),
        chunks=(CHUNK_SIZE, CHUNK_SIZE, 3),
        dtype=np.uint8,
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for image in tc.images:
            futures.append(executor.submit(fn, prefix, image))
        print("Submitted all futures")
        l = len(futures)
        t = tqdm.tqdm(total=l)
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            #print("Completed", i, "of", l)
            
            r = future.result()
            if r:
                filename, img, x, y, width, height = r 
            
                z[x : x + width, y : y + height, : ] += img
                counter[x : x + width, y : y + height, :] += 1    
         
            t.update(1)
            
    z = dask.array.from_array(z, chunks=(CHUNK_SIZE, CHUNK_SIZE, 3))
    counter = dask.array.from_array(counter, chunks=(CHUNK_SIZE, CHUNK_SIZE, 3))
    z = z // counter
    z = z.astype(dask.array.uint8)
    dask.array.to_zarr(dask.array.moveaxis(z, 2, 0), "test-2.zarr")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    prefix = pathlib.Path(sys.argv[1])
    # tile_config_to_tileconfiguration(prefix)
    # prefix = r"C:\Users\davidek\microscope_ui\controller\photo\1733112316.740324"
    main(prefix)
    # main("C:\\Users\\davidek\\Desktop\\1732488657.752864")
    # main("controller\\photo\\1732319758.459453")
