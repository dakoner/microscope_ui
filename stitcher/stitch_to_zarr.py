import glob
import dask.array
import signal
import pathlib
import sys
import zarr
import concurrent.futures
import tqdm
sys.path.insert(0, "controller")
import numpy as np
import shapely, shapely.geometry, shapely.strtree
from tile_configuration import (
    TileConfiguration,
    tile_config_to_shapely,
)
import sys
from util import get_image_data, CHUNK_SIZE


def fn(prefix, image):
    try:
        filename = pathlib.Path(prefix) / image.filename
        x = int(image.x)
        y = int(image.y)
        img = get_image_data(filename).swapaxes(0,1)

        width = img.shape[0]
        height = img.shape[1]
    except Exception as exc:
        print('%r generated an exception: %s' % (image, exc))
        return None
    return filename, img, x, y, width, height

def main(prefix):
    tc = TileConfiguration()
    fname = prefix / "TileConfiguration.sampled.txt"
    #if not fname.exists():
    #    tile_config_to_tileconfiguration(prefix)
    tc.load(fname)
    tc.move_to_origin()
    c = tile_config_to_shapely(prefix, tc)
    print(c.bounds)
    zarr_fname =  prefix / "test.zarr"
    counter_fname = prefix / "counter.zarr"
    if not zarr_fname.exists() and not counter_fname.exists():
        z = zarr.open(
            zarr_fname,
            mode="w",
            shape=(c.bounds[2], c.bounds[3], 3),
            chunks=(CHUNK_SIZE, CHUNK_SIZE, 3),
            dtype=np.uint16,
        )
        counter = zarr.open(
            counter_fname,
            mode="w",
            shape=(c.bounds[2], c.bounds[3], 3),
            chunks=(CHUNK_SIZE, CHUNK_SIZE, 3),
            dtype=np.uint8,
        )

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for image in tc.images:
                futures.append(executor.submit(fn, prefix, image))
            print("Submitted all futures")
            l = len(futures)
            t = tqdm.tqdm(total=l)
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                #print("Completed", i, "of", l)
                
                r = future.result()
                if r:
                    filename, img, x, y, width, height = r 
                
                    z[x : x + width, y : y + height, : ] += img
                    counter[x : x + width, y : y + height, :] += 1    
            
                t.update(1)
    else:
        z = zarr.open(
            zarr_fname,
            mode="r",
        )
        counter = zarr.open(
            counter_fname,
            mode="r",
        )
    final_zarr_fname = prefix / "test-2.zarr"
    if not final_zarr_fname.exists():
        z = dask.array.from_array(z, chunks=(CHUNK_SIZE, CHUNK_SIZE, 3))
        counter = dask.array.from_array(counter, chunks=(CHUNK_SIZE, CHUNK_SIZE, 3))
        z = z // counter
        z = z.astype(np.uint8)
        dask.array.to_zarr(dask.array.moveaxis(z, 2, 0), final_zarr_fname )


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    prefix = pathlib.Path(sys.argv[1])
    for dir_ in prefix.glob("*"):
        print(dir_)
        try:
            int(dir_.name)
        except ValueError:
            print("Skip", dir_)
        else:
            main(dir_)
