import concurrent.futures
import numpy as np
import tifffile
import sys
sys.path.append("..")
from microscope_ui.config import  WIDTH, HEIGHT, FOV_X, FOV_X_PIXELS, FOV_Y, FOV_Y_PIXELS
import zarr
from ome_zarr.io import parse_url
from ome_zarr.writer import write_image


def main():
    o=np.load("data.npy", allow_pickle=True)
    print(o.shape)
    # 0 1 2 3 4
    # T Z Y X C
    #
    o = o.transpose(0, 4, 1, 2, 3)
    print(o.shape)
    # T C Z Y X

    o = o[:10]
    store = parse_url("test.zarr", mode="w").store
    root = zarr.group(store=store)
    write_image(image=o, group=root, axes="tczyx", storage_options=dict(chunks=(1, 1, 1, 128, 128)))


if __name__ == '__main__':
    main()