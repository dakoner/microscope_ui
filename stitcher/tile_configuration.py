import shapely
from dataclasses import dataclass
import sys
import pandas as pd
from config import PIXEL_SCALE
import pathlib
from util import get_image_dimensions

@dataclass
class TileImage:
    filename: str
    x: float
    y: float


class TileConfiguration:
    def __init__(self):
        self.images = []

    def load(self, fname):
        with open(fname, "r") as r:
            for line in r.readlines():
                if line.startswith("#"):
                    continue
                if line.startswith("dim"):
                    continue
                if line.strip() == "":
                    continue
                fname, _, coords = line.split(";")
                t = str.maketrans("", "", " ()")
                coords = coords.translate(t)
                x, y = coords.split(",")
                x = float(x)
                y = float(y)
                self.addImage(filename=pathlib.Path(fname), x=x, y=y)

    def addImage(self, **kwargs):
        self.images.append(TileImage(**kwargs))

    def move_to_origin(self):
        x_min = min(x.x for x in self.images)
        y_min = min(x.y for x in self.images)
        for image in self.images:
            image.x = image.x - x_min
            image.y = image.y - y_min

    def scale(self, SCALE_X, SCALE_Y):
        for image in self.images:
            image.x = image.x * SCALE_X
            image.y = image.y * SCALE_Y

    def save(self, fname):
        s = ["dim=2"]
        for image in self.images:
            s.append(f"{image.filename}; ; ({image.x}, {image.y})")
        with open(fname, "w") as w:
            w.write("\n".join(s))


def tile_config_to_tileconfiguration(prefix):
    r = pd.read_json(f"{prefix}/tile_config.0.json", lines=True)
    r.set_index(["sequence"])
    tc = TileConfiguration()
    for row in r.itertuples():
        tc.addImage(filename=row.fname, x=row.x, y=row.y)
    tc.move_to_origin()
    tc.scale(1 / PIXEL_SCALE, 1 / PIXEL_SCALE)
    tc.save(f"{prefix}/TileConfiguration.txt")


def tile_config_to_shapely(prefix, tc):
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
    return c


if __name__ == "__main__":
    prefix = sys.argv[1]
    tile_config_to_tileconfiguration(prefix)
