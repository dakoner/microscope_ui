from pystackreg import StackReg
from skimage import io
from skimage.color import rgb2gray

#load reference and "moved" image
ref = rgb2gray(io.imread('controller\\photo\\1732508547.7836869\\test.1732508551.629935.png'))
mov = rgb2gray(io.imread('controller\\photo\\1732508547.7836869\\test.1732508553.477739.png'))

#Translational transformation
sr = StackReg(StackReg.TRANSLATION)
out_tra = sr.register_transform(ref, mov)
print(out_tra)
import pdb; pdb.set_trace()
