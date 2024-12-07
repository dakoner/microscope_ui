import pandas as pd
import json
import pathlib
import sys
import concurrent.futures

sys.path.insert(0, "controller")
from tile_configuration import TileConfiguration

prefix = pathlib.Path(
    "C:\\Users\\davidek\\microscope_ui\\controller\\photo\\1732508547.7836869"
)

tc = TileConfiguration()
tc.load(prefix / "TileConfiguration.registered.txt")
tc.move_to_origin()


def load(filename):
    with open(filename) as r:
        return json.load(r)

d = []

with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
    future_to_fname = {
        executor.submit(
            load,
            pathlib.Path("out")
            / image.filename.with_suffix(image.filename.suffix + ".json"),
        ): image.filename
        for image in tc.images
    }

    for future in concurrent.futures.as_completed(future_to_fname):
        filename = future_to_fname[future]
        results = future.result()
        for result in results:
            d.append( (filename, pathlib.Path(result), results[result][0], results[result][1]))
p = pd.DataFrame(d, columns=['fname1', 'fname2', 'tx', 'ty'])
p.set_index(["fname1", "fname2"], inplace=True)
p.drop(p['tx'] ** 2 + p['ty'] ** 2 == 0)
pass
    #     images[filename] = image
    # print(image.filename)
    # d[image.filename] = {}
    # p = pathlib.Path("out") / image.filename.with_suffix(image.filename.suffix + ".json")
    # with open(p) as r:
    #     j = json.load(r)
    #     for item in j:
    #         d[image.filename][pathlib.Path(item)] = j[item]
