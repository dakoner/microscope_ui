import tifffile
from lxml import etree
import requests

schemaAddr = "http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd"
content = requests.get(schemaAddr).content
schema = etree.fromstring(content)
xmlschema = etree.XMLSchema(schema)

with tifffile.TiffFile("z:\\test.ome.tiff") as t:
    o = t.ome_metadata.encode('utf-8')
    root = etree.fromstring(o)
    print(xmlschema.assertValid(root))
    with open("test.ome.xml", "wb") as f:
        f.write(etree.tostring(root, pretty_print=True))
