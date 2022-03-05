import pickle
import os
import subprocess
import numpy
import glob


fnames = glob.glob(r"z:\src\microscope_ui\movie/*.jpg")
cmd = ["c:\\Program Files\\Hugin\\bin\\pto_gen.exe", "-o", "initial.pto"]
cmd.extend(fnames)
subprocess.call(cmd)

files = [os.path.basename(fname)[:-4].split("_") for fname in fnames]
pto_vars = dict(zip(fnames, [(0, float(f[0]), float(f[1])) for f in files]))
 
f = open("pto_vars", "w")

for i, fname in enumerate(fnames):
    _, y, x = pto_vars[fname]
    f.write("TrX%d=%.3f,TrY%d=%.3f\n" % (i, y/1000., i, x/1000.))
f.close()
subprocess.call(["c:\\Program Files\\Hugin\\bin\\pto_var", "--set-from-file", "pto_vars", "-o", "initial_vars.pto", "initial.pto"])

#subprocess.call(['C:\\Program Files\\Hugin\\bin\\cpfind.exe',  '--prealigned', '-o', 'initial_vars_cpfind.pto', 'initial_vars.pto'])
