import sys
import glob
import json
import pandas as pd
sys.path.append("..")
from microscope_ui.config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE

def main():
    g = glob.glob("movie/*")
    g.sort()
    prefix = g[-1]
    d=json.load(open(f"{prefix}/scan_config.json"))
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    r.set_index(['counter', 'i', 'j', 'k'])

    f = open(f"{prefix}/TileConfiguration.txt", "w")
    f.write("dim=2\n")

    for row in r.itertuples():
        fname = row.fname
        x0 = row.x/PIXEL_SCALE
        y0 = row.y/PIXEL_SCALE
        #x0 = row.k * FOV_X_PIXELS
        #y0 = row.j * FOV_Y_PIXELS
        f.write(f"{fname}; ; ({x0}, {y0})\n")


if __name__ == '__main__':
    main()