
def render_intersection():
    with open("test.svg", "w") as w:
        width = c.bounds[2] - c.bounds[0]
        height = c.bounds[3] - c.bounds[1]
        w.write(
            f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink= "http://www.w3.org/1999/xlink" width="{width}" height="{height}">'
        )
        pxml = ET.fromstring(p.svg())
        pxml.attrib["fill"] = "#ffff00"
        w.write(ET.tostring(pxml).decode("utf-8"))
        bxml = ET.fromstring(b.svg())
        bxml.attrib["fill"] = "#0000ff"
        w.write(ET.tostring(bxml).decode("utf-8"))
        w.write(inter.svg())
        pts = shapely.box(*c.bounds)
        ptsxml = ET.fromstring(pts.svg())
        ptsxml.attrib["fill"] = "#ff0000"
        w.write(ET.tostring(ptsxml).decode("utf-8"))
        ixml = ET.fromstring(inter.svg())
        ixml.attrib["fill"] = "#00ff00"
        w.write(ET.tostring(ixml).decode("utf-8"))

        t = ET.Element("text")
        t.text = f"C({inter.bounds[0], inter.bounds[1]}) B{inter_in_box_coords.bounds[0], inter_in_box_coords.bounds[1]} CO{inter_in_chunk_coords.bounds[0], inter_in_chunk_coords.bounds[1]}"
        t.attrib["x"] = str(inter.bounds[0])
        t.attrib["y"] = str(inter.bounds[1])
        t.attrib["font-family"] = "sans-serif"
        t.attrib["font-size"] = "64px"
        w.write(ET.tostring(t).decode("utf-8"))
        t = ET.Element("text")
        t.text = f"C({inter.bounds[2], inter.bounds[3]}) B{inter_in_box_coords.bounds[2], inter_in_box_coords.bounds[3]} CO{inter_in_chunk_coords.bounds[2], inter_in_chunk_coords.bounds[3]}"
        t.attrib["x"] = str(inter.bounds[2])
        t.attrib["y"] = str(inter.bounds[3])
        t.attrib["font-family"] = "sans-serif"
        t.attrib["font-size"] = "64px"
        w.write(ET.tostring(t).decode("utf-8"))
        w.write("</svg>")