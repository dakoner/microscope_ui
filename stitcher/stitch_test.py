import PIL
import signal
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
from util import load_image, get_image_data, get_image_dimensions, CHUNK_SIZE


def do(polys, x, y, box_to_fname):
    try:
        b = shapely.geometry.box(x, y, x + CHUNK_SIZE, y + CHUNK_SIZE)
        results = np.zeros((CHUNK_SIZE, CHUNK_SIZE, 3), dtype=np.uint32)
        counter = np.zeros((CHUNK_SIZE, CHUNK_SIZE, 3), dtype=np.uint8)
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

            #print("Get iamge data for", x, y, box_to_fname[p])
            im = get_image_data(box_to_fname[p]).swapaxes(0,1)
            data = im[
                int(inter_in_box_coords[0]) : int(inter_in_box_coords[2]),
                int(inter_in_box_coords[1]) : int(inter_in_box_coords[3]),
            ]
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
        results = results.astype(np.uint8)
        fname = f"out\\temp.ome.{x},{y}.tif"
        tifffile.imwrite(
            fname,
            #results,
            results,
            #imagej=True,
            resolution=(833, 833),
            metadata={"unit": "mm", "axes": "CYX"},
        )
    except Exception as e:
        print("Except", e)
        import traceback
        traceback.print_exception(e)
    
    return x, y, results


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
    #da = np.zeros((bounds[0], bounds[1], 3), dtype=np.uint8)


    # for x in range(0, int(c.bounds[2]), CHUNK_SIZE):
    #     for y in range(0, int(c.bounds[3]), CHUNK_SIZE):
    #             x, y, results = do(polys, x, y, box_to_fname)
    #             print("Finished", x, y)

            
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for x in range(0, int(c.bounds[2]), CHUNK_SIZE):
            for y in range(0, int(c.bounds[3]), CHUNK_SIZE):
                futures.append(executor.submit(do, polys, x, y, box_to_fname))

        for future in concurrent.futures.as_completed(futures):
            x, y, results = future.result()
            print("Finished", x, y)
            #da[x : x + CHUNK_SIZE, y : y + CHUNK_SIZE, 3] = results


    #d.to_zarr("temp.zarr", compressor=Blosc(cname='zstd', clevel=3))

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    prefix = sys.argv[1]
    #prefix = r"C:\Users\davidek\microscope_ui\controller\photo\1732319758.459453"
    main(prefix)
    #main("C:\\Users\\davidek\\Desktop\\1732488657.752864")
    # main("controller\\photo\\1732319758.459453")
