import time
import shapely, shapely.geometry, shapely.strtree
import cv2
from tile_configuration import TileConfiguration
from PIL import Image
import sys
import concurrent.futures


def load_image(prefix, image):
    filename = f"{prefix}/{image.filename}"
    i = Image.open(filename)
    i = i.convert("L")
    return filename, image, i


def main():
    prefix = sys.argv[1]
    tc = TileConfiguration()
    tc.load(f"{prefix}/TileConfiguration.txt")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_image = {
            executor.submit(load_image, prefix, image): image for image in tc.images
        }

    polys = []
    for future in concurrent.futures.as_completed(future_to_image):
        fname = future_to_image[future]
        print(fname)
        filename, image, i = future.result()
        b = shapely.geometry.box(
            image.x, image.y, image.x + i.width, image.y + i.height
        )
        polys.append(b)

    c = shapely.geometry.MultiPolygon(polys)
    print("Full size", c.bounds)


main()
