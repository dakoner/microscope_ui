import glob
from skimage import registration, io
import numpy as np
import concurrent.futures
from itertools import product
from scipy import ndimage

def get_files():
    return sorted(glob.glob("movie/*jpg"))

def get_images(g):
    image_data = []

    for fname in g:
        img=io.imread(fname)
        image_data.append(img)

    return image_data

    
def pcc(image_data, index):
    i, j = index
    s, e, p  = registration.phase_cross_correlation(image_data[i], image_data[j], return_error=True, normalization=None)
    
    return s, e, p


def get_shifts(g, image_data):
    shifts = np.full((len(g), len(g), 3), 0., dtype=np.double)
    error = np.full((len(g), len(g)), 0, dtype=np.double)
    phasediff = np.full((len(g), len(g)), 0, dtype=np.double)


    r = range(len(g))
    c = product(r, repeat=2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # Start the load operations and mark each future with its index
        future_to_pcc = { executor.submit(pcc, image_data, index): index for index in c }
        
    for future in concurrent.futures.as_completed(future_to_pcc):
        index = future_to_pcc[future]

        try:
            s, e, p = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (index, exc))
        else:
            shifts[index], error[index], phasediff[index] = s, e, p


    return shifts, error, phasediff
