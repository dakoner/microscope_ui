from HersheyFonts import HersheyFonts
import numpy
import svgwrite
from svgwrite import mm

GRID_WIDTH=36
GRID_HEIGHT=36
SPACING=3.6

dwg= svgwrite.Drawing('test.svg', size=(GRID_WIDTH*mm,GRID_HEIGHT*mm))
# units are now mm
dwg.viewbox(width=GRID_WIDTH, height=GRID_HEIGHT)

# Existing frame
# r = dwg.rect(insert=(0,0), size=(GRID_WIDTH, GRID_HEIGHT), stroke='black', fill="none")
# dwg.add(r)

# #Sheet
# r = dwg.rect(insert=(0,0), size=(GRID_WIDTH, GRID_HEIGHT), stroke='black', fill="none", stroke_width="1")
# dwg.add(r)


for i in numpy.arange(0, GRID_HEIGHT, SPACING)[1:]:
    p = dwg.path(stroke='black', stroke_width=0.1, fill="none", d=('M', 0, i))
    p.push("l", GRID_WIDTH, 0)
    p.push("z")
    dwg.add(p)

for i in numpy.arange(0, GRID_WIDTH, SPACING)[1:]:
    p = dwg.path(stroke='black', stroke_width=0.1, fill="none", d=('M', i, 0))
    p.push("l", 0, GRID_HEIGHT)
    p.push("z")
    dwg.add(p)

thefont = HersheyFonts()
thefont.load_default_font()
thefont.normalize_rendering(1.5)
counter = 0
for i in numpy.arange(0, GRID_WIDTH+SPACING, SPACING)[1:]:
    for j in numpy.arange(0, GRID_HEIGHT+SPACING, SPACING)[1:]:
        g = dwg.add(dwg.g(transform="translate(%5.2f, %5.2f)" % (i-3, j-1)))
        for (x1, y1), (x2, y2) in thefont.lines_for_text("%02d" % counter):
            g.add(dwg.line((x1, -y1), (x2, -y2), stroke="black", stroke_width=0.05))
        counter += 1
dwg.save(pretty=True)
print("Done")
