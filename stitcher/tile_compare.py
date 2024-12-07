import os
import json
from PIL import Image
import numpy as np
import pathlib
import sys
import concurrent.futures
#from imreg_dft import translation
from skimage.registration import phase_cross_correlation
from skimage.transform import rescale
import imageio

sys.path.insert(0, "../controller")
from tile_configuration import TileConfiguration
sys.path.insert(0, "")
import imregpoc as imregpoc
from image_registration import chi2_shift
from image_registration.fft_tools import shift
import imageio.v3 as iio


def load_and_grayscale(filename):
    image = imageio.imread(filename)
    gray = np.dot(image, [0.2989, 0.5870, 0.1140])
    gray = np.round(gray).astype(np.uint8)
    return gray
    #return #rescale(gray, 1/SCALING)

def get_shift(i1, i2):
    # compute the cross-power spectrum of the two images:
    image_product = np.fft.fft2(i1) * np.fft.fft2(i2).conj()

    # compute the (not-normalized) cross-correlation between 
    # the two images:
    cc_image = np.fft.ifft2(image_product)

    # for visualization reasons, shift the zero-frequency 
    # component to the center of the spectrum:
    #cc_image_fftshift = np.fft.fftshift(cc_image)
    shape = i1.shape
    # find the peak in cc_image: 
    maxima = np.unravel_index(np.argmax(np.abs(cc_image)), shape)
    midpoints = np.array([np.fix(axis_size / 2) for axis_size in shape])
    float_dtype = image_product.real.dtype
    shifts = np.stack(maxima).astype(float_dtype, copy=False)
    shifts[shifts > midpoints] -= np.array(shape)[shifts > midpoints]
    #print(f"detected shifts: {shifts[1], shifts[0]}")
    return shifts

def main(prefix):
    tc = TileConfiguration()
    tc.load(f"{prefix}/TileConfiguration.registered.txt")
    tc.move_to_origin()
    images = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_to_fname = {executor.submit(load_and_grayscale, pathlib.Path(prefix) / image.filename): image.filename for image in tc.images if not os.path.exists(f"out/{image.filename}.json") }

        for future in concurrent.futures.as_completed(future_to_fname):
            filename = future_to_fname[future]
            image = future.result()
            images[filename] = image
            

    for fname1 in images:
        print(fname1)
        i1 = images[fname1]
        future_to_shift = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            for fname2 in images:
                i2 = images[fname2]
                future_to_shift[executor.submit(get_shift, i1, i2)] = fname2
                
            shifts = {}
            for future in concurrent.futures.as_completed(future_to_shift):
                fname2 = future_to_shift[future]
                result = future.result().tolist()
                if result != [0., 0.]:
                    shifts[str(fname2)] = result
            
            with open(f"out/{fname1}.json", "w") as w:
                w.write(json.dumps(shifts))
                
                
            

if __name__ == "__main__":
    #main(sys.argv[1])
    main("C:\\Users\\davidek\\microscope_ui\\controller\\photo\\1732508547.7836869")
