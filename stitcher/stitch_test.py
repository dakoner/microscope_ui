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
import dask.array as da
from functools import lru_cache

CHUNK_SIZE = 8192


def get_image_dimensions(filename):
    i = Image.open(filename)
    return i.width, i.height

def get_image_data(filename):
    im = Image.open(filename)
    im = im.convert("L")
    return np.asarray(im).T

@lru_cache
def load_image(prefix, image):
    filename = f"{prefix}/{image.filename}"
    i = Image.open(filename)
    i = i.convert("L")
    return filename, image, i


def do(polys, x, y, box_to_fname):
    b = shapely.geometry.box(x, y, x + CHUNK_SIZE, y + CHUNK_SIZE)
    results = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.uint64)
    counter = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.uint8)
    intersecting = []
    for p in polys:
        if b.intersects(p):
            intersecting.append(p)
    for p in intersecting:
        inter = b.intersection(p, grid_size=1)
        box_origin = sorted(p.exterior.coords)[0]
        inter_in_box_coords = shapely.transform(inter, lambda x: x - box_origin).bounds
        chunk_origin = x, y
        inter_in_chunk_coords = shapely.transform(
            inter, lambda x: x - chunk_origin
        ).bounds

        im = get_image_data(box_to_fname[p])
        data = im[
            int(inter_in_box_coords[0]) : int(inter_in_box_coords[2]),
            int(inter_in_box_coords[1]) : int(inter_in_box_coords[3]),
        ]
        del im
        results[
            int(inter_in_chunk_coords[0]) : int(inter_in_chunk_coords[2]),
            int(inter_in_chunk_coords[1]) : int(inter_in_chunk_coords[3]),
        ] += data
        counter[
            int(inter_in_chunk_coords[0]) : int(inter_in_chunk_coords[2]),
            int(inter_in_chunk_coords[1]) : int(inter_in_chunk_coords[3]),
        ] += 1

    results = results / counter
    results[np.isnan(results)] = 0
    return x, y, results


def round_up(val):
    x = int(val / CHUNK_SIZE)
    return CHUNK_SIZE * (x + 1)


def main(prefix):
    tc = TileConfiguration()
    tc.load(f"{prefix}/TileConfiguration.registered.txt")
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
    d = da.zeros(bounds, dtype=np.uint8)

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for x in range(0, int(c.bounds[2]), CHUNK_SIZE):
            for y in range(0, int(c.bounds[3]), CHUNK_SIZE):
                futures.append(executor.submit(do, polys, x, y, box_to_fname))

        for future in concurrent.futures.as_completed(futures):
            x, y, results = future.result()
            d[x : x + CHUNK_SIZE, y : y + CHUNK_SIZE] = results

    print("Write final image")
    tifffile.imwrite(
        "temp.ome.tif",
        da.flipud(d),
        imagej=True,
        resolution=(833, 833),
        metadata={"unit": "mm", "axes": "YX"},
    )


# main(sys.argv[1])
if __name__ == "__main__":
    main("controller\\photo\\1732256851.6429064")
    # main("controller\\photo\\1732319758.459453")
