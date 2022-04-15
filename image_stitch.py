import glob
import os
x_const = -3200
y_const = -3500
fnames = sorted(glob.glob("movie_grayscale/*.jpg"))
files = [os.path.basename(fname)[:-4].split("_") for fname in fnames]
a = [os.path.basename(fname) for fname in fnames]
b = [(float(f[1])*x_const,float(f[0])*y_const) for f in files]
pto_vars = dict(zip(a, b))

l = []
for fname, pos in pto_vars.items():
    l.append(f"{fname}; ; {pos}")

with open("movie_grayscale/TileConfiguration.txt", "w") as f:
    f.write("dim=2\n")
    f.write("\n".join(sorted(l)))
