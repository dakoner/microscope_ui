
"""Example:

dim=2
test.1732256857.9064806.jpg; ; (0.0, 0.0)
test.1732256859.3902438.jpg; ; (853.3333333333335, 0.0)
test.1732256860.879188.jpg; ; (1706.666666666667, 0.0)
test.1732256862.369296.jpg; ; (2560.0, 0.0)

"""
from dataclasses import dataclass
import sys
import pandas as pd
from config import PIXEL_SCALE

@dataclass
class TileImage:
    filename: str
    x: float
    y: float

class TileConfiguration:
    def __init__(self):
        self.images = []
    
    def load(self, fname):
        with open(fname, "r") as r:
            for line in r.readlines():
                if line.startswith("dim"):
                    continue
                fname, _, coords = line.split(";")
                t = str.maketrans('', '', " ()")
                coords = coords.translate(t)
                x, y = coords.split(",")
                x = float(x)
                y = float(y)
                tc.addImage(filename=fname, x=x, y=y)
        
    def addImage(self, **kwargs):
        self.images.append(TileImage(**kwargs))
        
    def move_to_origin(self):
        x_0 = self.images[0].x
        y_0 = self.images[0].y
        for image in self.images:
            image.x = image.x - x_0
            image.y = image.y - y_0
            
    def scale(self, SCALE_X, SCALE_Y):
        for image in self.images:
            image.x = image.x * SCALE_X
            image.y = image.y * SCALE_Y
            
    def save(self, fname):
        s = [ "dim=2" ]
        for image in self.images:
            s.append(f"{image.filename}; ; ({image.x}, {image.y})")
        with open(fname, "w") as w:
            w.write("\n".join(s))
        
if __name__ == '__main__':
    # prefix = sys.argv[1]
    # r = pd.read_json(f"{prefix}/tile_config.json", lines=True)
    # r.set_index(["i", "j", "k"])
    # tc = TileConfiguration()
    # for row in r.itertuples():
    #     tc.addImage(filename=row.fname, x=row.x, y=row.y)
    # tc.move_to_origin()
    # tc.scale(1/PIXEL_SCALE, 1/PIXEL_SCALE)
    # tc.save(f"{prefix}/TileConfiguration.txt")
    
    
    tc = TileConfiguration()
    tc.load(f"{sys.argv[1]}/TileConfiguration.txt")
    tc.save(f"{sys.argv[1]}/TileConfiguration.mine.txt")
