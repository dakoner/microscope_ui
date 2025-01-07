#!/usr/bin/env python


import pandas as pd
import matplotlib.pyplot as plt
import glob
import pathlib
import ffmpeg
import numpy as np
from PIL import Image
import sys
import sys
sys.path.insert(0, "../controller")
import tile_configuration
from config import PIXEL_SCALE
from util import get_image_dimensions
import shapely

def get_latest_movie():
    g = glob.glob("../controller/movie/*")
    s = sorted(g, key=lambda x: float(x.split("\\")[-1]))
    d = pathlib.Path(s[-1])
    return d

def get_strips(prefix):
    g = prefix.glob("*")
    strips = []
    for item in g:
        try:
            int(item.name)
            strips.append(item)
        except ValueError:
            pass
    return sorted(strips, key=lambda x: int(x.name))


def load_tile_config_json(strip):
    r = pd.read_json(strip / "tile_config.json", lines=True)
    r.set_index(["sequence"])
    return r

def create_tile_config(r):
    tc = tile_configuration.TileConfiguration()
    for row in r.itertuples():
        tc.addImage(filename=row.fname, x=row.x, y=row.y)
    tc.move_to_origin()
    tc.scale(1 / PIXEL_SCALE, 1 / PIXEL_SCALE)
    return tc
    #tc.save(prefix / str(k) / "TileConfiguration.txt")


def extract_images(strip):
    movie_fname = strip / "test.mkv"
    process = (
        ffmpeg.
        input(
            movie_fname,)
        .output(
            "pipe:", format="rawvideo", pix_fmt="rgb24"
        )  
        .run_async(pipe_stdout=True)
        )

    for item in r['sequence'].to_list():
        s = process.stdout.read(1280*720*3)
        if len(s) == 0:
            print("eof")
            break
        n = np.frombuffer(s, np.uint8).reshape(720, 1280, 3)
        i = Image.fromarray(n)
        # should be pulling fname from the dataframe
        fname = strip / "images" / ("test.%05d.tif" % item)
        i.save(fname)


def images_to_polytree(strip, tc):
    polys = []
    box_to_fname = {}
    for image in tc.images:
        filename = pathlib.Path(strip) / image.filename
        width, height = 1280, 720 # get_image_dimensions(filename)

        b = shapely.geometry.box(
            int(image.x), int(image.y), int(image.x) + width, int(image.y) + height
        )
        box_to_fname[b] = filename
        polys.append(b)

    tree = shapely.strtree.STRtree(polys)

    return polys, tree, box_to_fname

def frames_to_keep(tc, polys, tree, box_to_fname):      
    df = pd.DataFrame(tc.images)
    intersections = []
    mid_x = 1280/2
    keep_fnames = []
    for y in np.arange(df["y"].min(), df["y"].max(), 720/2):
        p = shapely.geometry.point.Point(mid_x, y)
        overlapping_polygons = tree.query(p)
        middle_poly = overlapping_polygons[0]
        path = pathlib.Path(box_to_fname[polys[middle_poly]])
        fname = pathlib.Path(*path.parts[-2:]).with_suffix(".tif")
        keep_fnames.append(fname)
        #print()
    return keep_fnames

def create_sampled_tile_config(strip, tc, keep_fnames):
    new_images = []
    for image in tc.images:
        image.filename = pathlib.Path(image.filename).with_suffix(".tif")
        if image.filename in keep_fnames:
            new_images.append(image)

    new_tc = tile_configuration.TileConfiguration()
    new_tc.images = new_images
    new_tc.save(strip / "TileConfiguration.sampled.txt")     
    
def main():

    prefix = get_latest_movie()
    strips = get_strips(prefix)

    for strip in strips:

        print(strip)
        images_path = strip / "images"
        images_path.mkdir(exist_ok=True)
        r = load_tile_config_json(strip)
        tc = create_tile_config(r)
        #extract_images(strip, tc, keep_fnames)
        polys, tree, box_to_fname = images_to_polytree(strip, tc)
        keep_fnames = frames_to_keep(tc, polys, tree, box_to_fname)
        print(len(keep_fnames))
        create_sampled_tile_config(strip, tc, keep_fnames)
        
if __name__ == '__main__':
    main()
  



# # In[37]:


# df = pd.read_json(d, lines=True, orient='records')
# df.index = df["sequence"]
# df["timestamp"] = pd.to_datetime(df['tv_sec'], unit='s') + pd.to_timedelta(df['tv_nsec'], unit='ns')
# df.drop("tv_sec", axis=1, inplace=True)
# df.drop("tv_nsec", axis=1, inplace=True)

# df['timestamp_shift'] = df['timestamp'].shift()
# df['timestamp_delta'] = df['timestamp'] - df['timestamp_shift']


# # In[38]:


# get_ipython().run_line_magic('matplotlib', 'inline')
# #df.plot(y="timestamp_delta")
# df['timestamp_delta'].dt.microseconds.hist(bins=100)
# plt.show()

