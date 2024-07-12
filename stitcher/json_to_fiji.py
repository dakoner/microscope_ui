import sys
import glob
import json
import pandas as pd
sys.path.append("..")
from microscope_ui.config import HEIGHT, WIDTH, FOV_X_PIXELS, FOV_Y_PIXELS, PIXEL_SCALE

def main():
    #g = glob.glob(sys/argv[1] + "/*.jpg")
    #g.sort()
    #prefix = g[-1]
    #d=json.load(open(f"{prefix}/scan_config.json"))
    #import glob
    #g = glob.glob("photo/*")
    prefix = "photo\\test2"
    #prefix = sorted(g, key=lambda x: float(x.split("/")[1]))[-1]
    r=pd.read_json(f"{prefix}/tile_config.json", lines=True)
    r.set_index(['i', 'j', 'k'])

    f = open(f"{prefix}/TileConfiguration.txt", "w")
    f.write("dim=2\n")

    first = True
    for row in r.itertuples():
        fname = row.fname
        if first:
            x_0 =  row.x/PIXEL_SCALE
            y_0 = row.y/PIXEL_SCALE
        x = row.x/PIXEL_SCALE - x_0
        y = row.y/PIXEL_SCALE- y_0
      
        first = False
        f.write(f"{fname}; ; ({x}, {y})\n")


if __name__ == '__main__':
    main()