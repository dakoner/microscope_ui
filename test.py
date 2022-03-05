import numpy as np

half_fov = 1
pos0 = (-1,1.1)
pos1 = (-1,1.1)
xs = np.arange(min(pos0[0], pos0[1]), max(pos0[0], pos0[1]), half_fov)
#print(xs)
ys = np.arange(min(pos1[0], pos1[1]), max(pos1[0], pos1[1]), half_fov)
#print(ys)
xx, yy = np.meshgrid(xs, ys)

s_grid = np.vstack([xx.ravel(), yy.ravel()])

print(s_grid.reshape(3,3,2))