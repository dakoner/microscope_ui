import zarr
import pathlib
import sys
import dask.array
import numpy as np

def is_an_int(i):
    try:
        int(i)
    except ValueError:
        return False
    else:
        return True


def main():
    prefix = pathlib.Path(sys.argv[1])
    dirs = []
    for dir_ in prefix.glob("*"):
        try:
            int(dir_.name)
        except ValueError:
            print("Skip", dir_)
        else:
            dirs.append(dir_)
    z = []
    shapes = []
    dirs.sort(key = lambda x: int(x.name))
    print(dirs)
    for dir_ in dirs:
        print(dir_ / "test-2.zarr")
        o = zarr.open(dir_ / "test-2.zarr")
        if len(o):
            z.append(o)
            shapes.append(o.shape)
    n = np.array(shapes)
    smallest = n[:,2].min()
    new = []
    for item in z:
        new_ = item[:, :, :smallest]
        new.append(np.flip(new_, axis=1))
        
    d = dask.array.concatenate(new, 1)
    dask.array.to_zarr(d, "test.zarr")


if __name__ == "__main__":
    main()
