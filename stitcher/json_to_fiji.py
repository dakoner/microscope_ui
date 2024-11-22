import sys
import glob
import json
import pandas as pd
from config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE


def main():
    prefix = sys.argv[1]
    r = pd.read_json(f"{prefix}/tile_config.json", lines=True)
    r.set_index(["i", "j", "k"])

    f = open(f"{prefix}/TileConfiguration.txt", "w")
    f.write("dim=2\n")

    first = True
    for row in r.itertuples():
        fname = row.fname
        if first:
            x_0 = row.x / PIXEL_SCALE
            y_0 = row.y / PIXEL_SCALE
        x = row.x / PIXEL_SCALE - x_0
        y = row.y / PIXEL_SCALE - y_0

        first = False
        f.write(f"{fname}; ; ({x}, {y})\n")


if __name__ == "__main__":
    main()
