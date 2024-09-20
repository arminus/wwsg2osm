import os

with open(f'./output/osm_patch_ids.txt') as f:
    mapping_table = f.readlines()

"""
before running this script in JOSM, download data from Overpass:

[out:xml][timeout:90][bbox:45.859412,8.283691,49.253465,17.380371];
(
  way["protect_class"="14"];
  relation["protect_class"="14"];
);
(._;>;);
out meta;

which is basically B/A/CH

"""

# see https://github.com/Gubaer/josm-scripting-plugin/issues/97
js_init = """import josm from 'C:\\\\Data\\\\Development\\\\OSM\\\\Josm\\\\josm\\\\josm.mjs';
import { buildChangeCommand } from 'C:\\\\Data\\\\Development\\\\OSM\\\\Josm\\\\josm\\\\josm\\\\command.mjs';
import { DataSetUtil, OsmPrimitiveType} from 'C:\\\\Data\\\\Development\\\\OSM\\\\Josm\\\\josm\\\\josm\\\\ds.mjs';

const layer = josm.layers.activeLayer;
const dsutil = new DataSetUtil(layer.data);
let primitive

"""

with open('./output/josm.js', 'w') as f:
    f.write(js_init)
    for osm in mapping_table:
        type = os.path.dirname(osm)
        osm_id = os.path.basename(osm).strip()
        if type == "way":
            f.write(f'primitive =  dsutil.get({osm_id}, OsmPrimitiveType.WAY);\n')
        else:
            f.write(f'primitive =  dsutil.get({osm_id}, OsmPrimitiveType.RELATION);\n')
        f.write('if (primitive) {\n')
        f.write('  buildChangeCommand(primitive, {tags: {"seasonal": "winter"}}).applyTo(layer);\n')
        f.write('  buildChangeCommand(primitive, {tags: {"access": null}}).applyTo(layer);\n')
        f.write('  buildChangeCommand(primitive, {tags: {"access:conditional": "discouraged @ (Dec 01-Apr 30)"}}).applyTo(layer);\n')
        f.write('}\n')
