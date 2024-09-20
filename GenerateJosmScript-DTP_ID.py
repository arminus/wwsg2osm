import os

# as produced by GeoJsonDiff
with open(f'./output/osm2dtp_mapping.csv') as f:
    mapping_table = f.readlines()

"""
before running this script in JOSM, download data from Overpass:

[out:xml][timeout:90];
{{geocodeArea:"Bayern"}}->.searchArea;
(
  way["protect_class"="14"](area.searchArea);
  relation["protect_class"="14"](area.searchArea);
);
(._;>;);
out meta;

or

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
    for line in mapping_table:
        osm, dtp_id = line.split(';')
        type = os.path.dirname(osm)
        osm_id = os.path.basename(osm)
        dtp_id = dtp_id.replace('\n', '')
        if type == "way":
            f.write(f'primitive =  dsutil.get({osm_id}, OsmPrimitiveType.WAY);\n')
        else:
            f.write(f'primitive =  dsutil.get({osm_id}, OsmPrimitiveType.RELATION);\n')
        f.write('if (primitive && !primitive.getKeys().get("dtp_id")) { buildChangeCommand(primitive, {tags: {dtp_id: "'+dtp_id+'"}}).applyTo(layer); }\n')

        # delete command
        # f.write('if (primitive.getKeys().get("dtp_id")) { buildChangeCommand(primitive, {tags: {"dtp_id": null}}).applyTo(layer); }\n');