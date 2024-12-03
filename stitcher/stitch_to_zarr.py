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
from tile_configuration import TileConfiguration, tile_config_to_tileconfiguration
from PIL import Image
import sys
import concurrent.futures
from util import get_image_data, get_image_dimensions, CHUNK_SIZE
import threading

# l = threading.Lock()

# def round_up(val):
#     x = int(val / CHUNK_SIZE)
#     return CHUNK_SIZE * (x + 1)


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
            int(image.x), int(image.y), int(image.x) + width, int(image.y) + height
        )
        box_to_fname[b] = filename
        polys.append(b)

    c = shapely.geometry.GeometryCollection(polys)

    z = zarr.open(
        "test.zarr",
        mode="w",
        shape=(c.bounds[2], c.bounds[3], 3),
        chunks=(CHUNK_SIZE, CHUNK_SIZE),
        dtype=np.uint16,
    )
    counter = zarr.open(
        "counter.zarr",
        mode="w",
        shape=(int(c.bounds[2]), int(c.bounds[3]), 3),
        chunks=(CHUNK_SIZE, CHUNK_SIZE),
        dtype=np.uint8,
    )

    for image in tqdm.tqdm(tc.images):
        filename = pathlib.Path(prefix) / image.filename
        img = get_image_data(filename).swapaxes(0, 1)
        x = int(image.x)
        y = int(image.y)
        width = img.shape[0]
        height = img.shape[1]
        z[x : x + width, y : y + height :] += img
        counter[x : x + width, y : y + height] += 1

    z = dask.array.from_array(z, chunks=(CHUNK_SIZE, CHUNK_SIZE, 3))
    counter = dask.array.from_array(counter, chunks=(CHUNK_SIZE, CHUNK_SIZE, 3))
    z = z // counter
    z = z.astype(dask.array.uint8)
    z = dask.array.moveaxis(z, 2, 0)
    dask.array.to_zarr(z, "test-2.zarr")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    prefix = sys.argv[1]
    tile_config_to_tileconfiguration(prefix)
    # prefix = r"C:\Users\davidek\microscope_ui\controller\photo\1733112316.740324"
    main(prefix)
    # main("C:\\Users\\davidek\\Desktop\\1732488657.752864")
    # main("controller\\photo\\1732319758.459453")
