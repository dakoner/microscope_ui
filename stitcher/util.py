import shapely
import pathlib
from functools import lru_cache
from PIL import Image
import numpy as np
CHUNK_SIZE = 1024

def get_image_dimensions(filename):
    i = Image.open(filename)
    return i.width, i.height


@lru_cache(maxsize=32)
def get_image_data(filename):
    im = Image.open(filename)
    #im = im.convert("L")
    return np.asarray(im)


def load_image(prefix, image):
    filename = f"{prefix}/{image.filename}"
    i = Image.open(filename)
    i = i.convert("L")
    return filename, image, i


def tile_config_to_shapely(prefix, tc):
    polys = []
    poly_to_fname = {}

    for image in tc.images:
        filename = pathlib.Path(prefix) / image.filename
        width, height = get_image_dimensions(filename)
        b = shapely.geometry.box(
            int(image.x),
            int(image.y),
            int(image.x) + width,
            int(image.y) + height,
        )
        poly_to_fname[b] = image.filename
        polys.append(b)

    return polys, poly_to_fname


def polys_to_intersections(polys):
    intersections = []
    tree = shapely.strtree.STRtree(polys)

    for polygon in polys:
        overlapping_polygons = tree.query(polygon)
        for i in overlapping_polygons:
            overlapping_polygon = polys[i]
            if polygon != overlapping_polygon and polygon.overlaps(overlapping_polygon):
                intersections.append((polygon, overlapping_polygon))

    return intersections
