import dask.array as da
import numpy as np
from numcodecs import Blosc
import tifffile
fname = "test.tif"
d = tifffile.imread(fname)
da.array(np.moveaxis(d, 2, 0)).to_zarr("temp.zarr", compressor=Blosc(cname='zstd', clevel=3))