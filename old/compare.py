import glob
from skimage import registration, io
import numpy as np

g = sorted(glob.glob("movie/*jpg"))
shifts = np.full((len(g), len(g), 3), np.nan, dtype=np.double)
error = np.full((len(g), len(g)), np.nan, dtype=np.double)
phasediff = np.full((len(g), len(g)), np.nan, dtype=np.double)

image_data = []

for fname in g:
    img=io.imread(fname)
    image_data.append(img)

for i in range(len(g)):
    for j in range(len(g)):
        if i == j:
            continue
        s, e, p  = registration.phase_cross_correlation(image_data[i], image_data[j], return_error=True, upsample_factor=2, normalization=None)
        if not np.all(s == 0.0):
            shifts[i, j] = s
            error[i, j] = e
            phasediff[i, j] = p
            print(i, j, s, e, p)

