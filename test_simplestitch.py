import concurrent.futures
import numpy as np
import tifffile
from config import  WIDTH, HEIGHT, FOV_X, FOV_X_PIXELS, FOV_Y, FOV_Y_PIXELS


def poke(f, o, d):

    p = eval(f)
    h0 = p[2]*FOV_Y_PIXELS
    w0 = p[3]*FOV_X_PIXELS
    o[p[0], p[1], :, h0:h0+HEIGHT, w0:w0+WIDTH] = d[f]
#     T      Z    C  Y              X           
    return True

def main():
    d=np.load("data.npz", allow_pickle=True)
    r = []
    for f in d.files:
        r.append(eval(f))
    max_t = max(r, key=lambda x: x[0])[0]
    max_z = max(r, key=lambda x: x[1])[1]
    max_y = max(r, key=lambda x: x[2])[2]
    max_x = max(r, key=lambda x: x[3])[3]
    max_c = 3

    y_size = max_y*FOV_Y_PIXELS+HEIGHT
    x_size = max_x*FOV_X_PIXELS+WIDTH

    # TCZYX
    o = np.zeros(shape=(max_t+1, max_z+1, max_c, y_size, x_size), dtype=np.ubyte)
    l = list(d.files)


    # with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    #     future_to_pcc = { executor.submit(poke, f, o, d): index for index in l }

    # counter = 0
    # for future in concurrent.futures.as_completed(future_to_pcc):
    #     index = future_to_pcc[future]
    #     try:
    #         print(index, future.result())
    #     except Exception as exc:
    #         print('%r generated an exception: %s' % (index, exc))
    #     else:
    #         counter += 1
    #         print("good job", counter)

    #print(counter, len(l))
    for i, f in enumerate(l):
        print(i, i/len(l))
        poke(f, o, d)
        

    #tifffile.imwrite('temp.tif', o, imagej=True,
    #    metadata={
    ##        'finterval': 1,
    #        'axes': 'TZCYX',
    #    })
    with tifffile.TiffWriter('temp.ome.tif', bigtiff=True) as tif:
        metadata={
            'axes': 'TZCYX',
            'Channel': {'Name': ['Red', 'Green', 'Blue']},
            'TimeIncrement': 0.1,
            'TimeIncrementUnit': 's',
            'PhysicalSizeX': 1,
            'PhysicalSizeXUnit': 'Âµm',
            'PhysicalSizeY': 1,
            'PhysicalSizeYUnit': 'Âµm',
            'UUID': '5'
        }
        options = dict(
            photometric='rgb',
            tile=(128, 128),
            compression='jpeg',
            resolutionunit='CENTIMETER'
        )
        #import pdb; pdb.set_trace()
        tif.write(
            o,
            resolution=(1e4 / 1, 1e4 / 1),
            metadata=metadata,
            **options
        )

if __name__ == '__main__':
    main()