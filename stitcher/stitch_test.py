from lxml import etree as ET
import sys

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


def load_image(prefix, image):
    filename = f"{prefix}/{image.filename}"
    i = Image.open(filename)
    i = i.convert("L")
    return filename, image, i


def render_intersection():
    with open("test.svg", "w") as w:
        width = c.bounds[2] - c.bounds[0]
        height = c.bounds[3] - c.bounds[1]
        w.write(
            f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink= "http://www.w3.org/1999/xlink" width="{width}" height="{height}">'
        )
        pxml = ET.fromstring(p.svg())
        pxml.attrib["fill"] = "#ffff00"
        w.write(ET.tostring(pxml).decode("utf-8"))
        bxml = ET.fromstring(b.svg())
        bxml.attrib["fill"] = "#0000ff"
        w.write(ET.tostring(bxml).decode("utf-8"))
        w.write(inter.svg())
        pts = shapely.box(*c.bounds)
        ptsxml = ET.fromstring(pts.svg())
        ptsxml.attrib["fill"] = "#ff0000"
        w.write(ET.tostring(ptsxml).decode("utf-8"))
        ixml = ET.fromstring(inter.svg())
        ixml.attrib["fill"] = "#00ff00"
        w.write(ET.tostring(ixml).decode("utf-8"))

        t = ET.Element("text")
        t.text = f"C({inter.bounds[0], inter.bounds[1]}) B{inter_in_box_coords.bounds[0], inter_in_box_coords.bounds[1]} CO{inter_in_chunk_coords.bounds[0], inter_in_chunk_coords.bounds[1]}"
        t.attrib["x"] = str(inter.bounds[0])
        t.attrib["y"] = str(inter.bounds[1])
        t.attrib["font-family"] = "sans-serif"
        t.attrib["font-size"] = "64px"
        w.write(ET.tostring(t).decode("utf-8"))
        t = ET.Element("text")
        t.text = f"C({inter.bounds[2], inter.bounds[3]}) B{inter_in_box_coords.bounds[2], inter_in_box_coords.bounds[3]} CO{inter_in_chunk_coords.bounds[2], inter_in_chunk_coords.bounds[3]}"
        t.attrib["x"] = str(inter.bounds[2])
        t.attrib["y"] = str(inter.bounds[3])
        t.attrib["font-family"] = "sans-serif"
        t.attrib["font-size"] = "64px"
        w.write(ET.tostring(t).decode("utf-8"))
        w.write("</svg>")


def main(prefix):
    tc = TileConfiguration()
    tc.load(f"{prefix}/TileConfiguration.registered.registered.txt")
    tc.move_to_origin()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_image = {
            executor.submit(load_image, prefix, image): image for image in tc.images
        }

    box_to_fname = {}
    box_to_image = {}

    polys = []
    for future in concurrent.futures.as_completed(future_to_image):
        fname = future_to_image[future]
        filename, image, i = future.result()
        b = shapely.geometry.box(
            int(image.x), int(image.y), int(image.x) + i.width, int(image.y) + i.height
        )
        box_to_fname[b] = filename
        box_to_image[b] = np.asarray(i).T
        polys.append(b)

    c = shapely.geometry.GeometryCollection(polys)
    # with open("test.svg", "w") as w:
    #     w.write('<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink= "http://www.w3.org/1999/xlink">')
    #     w.write(c.svg())
    #     w.write('</svg>')

    print("Full size", c.bounds)

    # iterate over chunks from the full size image
    # find all the intersecting polys
    # composite the chunk from the intersecting polys
    CHUNK_SIZE = 2000
    d = da.zeros((c.bounds[2], c.bounds[3]), dtype=np.uint8)
    for i, x in enumerate(range(0, int(c.bounds[2]), CHUNK_SIZE)):
        for j, y in enumerate(range(0, int(c.bounds[3]), CHUNK_SIZE)):
            b = shapely.geometry.box(x, y, x + CHUNK_SIZE, y + CHUNK_SIZE)
            print("i,j", i, j, x, y)
            print("Chunk", b.bounds)  # chunk in pixel coordinates
            results = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.uint64)
            counter = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.uint8)
            intersecting = []
            for p in polys:
                if b.intersects(p):
                    intersecting.append(p)
            for p in intersecting:
                inter = b.intersection(p, grid_size=1)
                box_origin = sorted(p.exterior.coords)[0]
                inter_in_box_coords = shapely.transform(
                    inter, lambda x: x - box_origin
                ).bounds
                chunk_origin = x, y
                inter_in_chunk_coords = shapely.transform(
                    inter, lambda x: x - chunk_origin
                ).bounds
                # print("\tinter", inter)
                # print("\tPolygon", p)
                # print("\tbox_origin", box_origin)
                # print("\tinter in box coords", inter_in_box_coords)
                # print("\tchunk_origin", chunk_origin)
                # print("\tinter in chunk coords", inter_in_box_coords)

                im = box_to_image[p]
                data = im[
                    int(inter_in_box_coords[0]) : int(inter_in_box_coords[2]),
                    int(inter_in_box_coords[1]) : int(inter_in_box_coords[3]),
                ]
                results[
                    int(inter_in_chunk_coords[0]) : int(inter_in_chunk_coords[2]),
                    int(inter_in_chunk_coords[1]) : int(inter_in_chunk_coords[3]),
                ] += data
                counter[int(inter_in_chunk_coords[0]) : int(inter_in_chunk_coords[2]),
                    int(inter_in_chunk_coords[1]) : int(inter_in_chunk_coords[3])] += 1
            im = Image.fromarray(np.uint8(counter))
            im.save(f"out\\counter.{i},{j}.png")
            results = results / counter
            results[np.isnan(results)] = 0

            im = Image.fromarray(np.uint8(results))
            im.save(f"out\\chunk.{i},{j}.png")

            if x + CHUNK_SIZE > d.shape[0]:
                max_x = d.shape[0]
            else:
                max_x = x + CHUNK_SIZE
            if y + CHUNK_SIZE > d.shape[1]:
                max_y = d.shape[1]
            else:
                max_y = y + CHUNK_SIZE

            d[x:max_x, y:max_y] = results[: max_x - x, : max_y - y]
    im = Image.fromarray(d.compute())
    im.save("final.png")


# main(sys.argv[1])
main("controller\\photo\\1732319758.459453")
