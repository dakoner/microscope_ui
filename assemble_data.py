import pandas as pd
import numpy as np
import tifffile
from config import FOV_X_PIXELS, FOV_Y_PIXELS, WIDTH, HEIGHT # should obtain from movie json.

adj_FOV_Y_PIXELS=FOV_Y_PIXELS+5
def get_data():
    prefix = "z:\\src\\microscope_ui"
    r = pd.read_json(f"{prefix}\\movie\\1668311323\\tile_config.json", lines=True)
    r.set_index(['acquisition_counter', 'gx', 'gy', 'gz'])
    os = []
    t_max = len(r.acquisition_counter.unique())
    z_max = len(r.gz.unique())
    x_max = r.gx.max()*FOV_X_PIXELS+WIDTH
    y_max = r.gy.max()*adj_FOV_Y_PIXELS+HEIGHT
    c_max = 3 
    o = np.zeros(shape=(t_max, z_max, y_max, x_max, c_max), dtype=np.ubyte)
    for t in r.acquisition_counter.unique():
        print(t)
        # Get all items in time t
        d = r[r.acquisition_counter == t]


        # We now have all the CZYX data for a time

        for row in d.itertuples():
            fname = row.fname
            data = tifffile.imread(f"{prefix}/{row.fname}")
            x0 = row.gx * FOV_X_PIXELS
            y0 = row.gy * adj_FOV_Y_PIXELS
            x1 = x0 + WIDTH
            y1 = y0 + HEIGHT
            o[t, row.gz, y0:y1, x0:x1] = data
    return o

if __name__ == '__main__':
    o = get_data()
    # T Z Y X C
    np.save("c:\\Users\\dek\\Desktop\\data.npy", o)
    o2 = o[:, 0, :, :, 0]
    np.save("c:\\Users\\dek\\Desktop\\data2.npy", o2)
