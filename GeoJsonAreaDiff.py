import os, sys
import fiona
from tqdm import tqdm
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.geometry import Polygon
import requests

osm_file = './Schongebiete.geojson'
response = requests.get('https://www.xctrails.org/osm/Schongebiete.geojson')
if response.status_code == 200:
    with open(osm_file, 'wb') as file:
        file.write(response.content)
else:
    print(f"Failed to download file: {response.status_code}")
    sys.exit(1)

# produced by DTPAreas2GeoJson.py
newFile = './geojson/cat_18-19.geojson'
# newFile = './geojson/cat_20-41.geojson'

if not os.path.exists('./output'): os.mkdir('./output')
newAreasFile = './output/new-areas.geojson'
newAreasFileJosm = './output/new-areas-josm.geojson'
mappingFile = './output/osm2dtp_mapping.csv'

# areasIdenticalFile = './output/same-areas.geojson'

oldFeatures = []
with fiona.open(osm_file) as input:
    oldCrs = input.crs
    for feat in input:
        oldFeatures.append(feat)
print(f"OSM-Gebiete in {osm_file}: {len(oldFeatures)}")

newFeatures = []
with fiona.open(newFile) as input:
    schema = input.schema
    for feat in input:
        if len(feat['geometry']['coordinates']) > 1:
            # FIXME: multipolygons - code to be improved...
            for pfeat in feat['geometry']['coordinates']:
                try: # some are len(1) lists, some aren't ?!
                    poly = Polygon(pfeat[0])
                except:
                    poly = Polygon(pfeat)
                poly = transform(lambda x, y, z=None: (x, y), poly)
                newFeatures.append({
                    'type': 'Feature',
                    'geometry': mapping(poly),
                    'properties': feat['properties']
                })
            continue
        if len(feat['geometry']['coordinates'][0]) < 3:
            print("Skipping 2-point line")
            continue
        # transform 3D to 2D
        poly = shape(feat['geometry'])
        poly = transform(lambda x, y, z=None: (x, y), poly)
        newFeatures.append({
            'type': 'Feature',
            'geometry': mapping(poly),
            'properties': feat['properties']
        })

size = len(newFeatures);          
print(f"Gebiete in {newFile}: {size}")

# https://www.reddit.com/r/gis/comments/mcw0y0/comparing_two_linestrings_with_shapely/

newCount = 0 
foundCount = 0
newFeaturesOut = []
sameFeatures = []

def get_iou( polygon1, polygon2):
    if polygon1.intersects(polygon2): 
        intersect = polygon1.intersection(polygon2).area
        union = polygon1.union(polygon2).area
        return intersect/union
    return 0

print("Calculating diffs...")

mismatched_osm_ids = []
mapping_table = []

with tqdm(total=len(newFeatures)) as pbar:
    for newFeature in newFeatures:
        pbar.update(1)
        # apply a buffer to avoid TopologyException: Input geom 1 is invalid: Self-intersection at or near point
        # https://www.programmersought.com/article/69515213493/
        if 'osm_id' in newFeature['properties']:
            dtp_osm_id = newFeature['properties']['osm_id'].replace('https://www.openstreetmap.org/','')
        else:
            dtp_osm_id = "undefined";
        newGeom = Polygon(shape(newFeature['geometry']).exterior)
        newGeomB = newGeom.buffer(0.0001)
        found = False
        iou = 0
        for oldFeature in oldFeatures:
            try:
                oldGeom = Polygon(shape(oldFeature['geometry']))
                oldGeomB = oldGeom.buffer(0.0001)
            except Exception as ex:
                # FIXME: 'MultiPolygon' object has no attribute 'exterior' - why ?!?! - MultiPolygons get removed above?!
                # also: linearring requires at least 4 coordinates. ?!?!
                # print(ex)
                # print(oldFeature['geometry'])
                continue
            # https://www.pyimagesearch.com/2016/11/07/intersection-over-union-iou-for-object-detection/
            iou = get_iou(newGeomB, oldGeomB)
            if iou > 0.985: # baseline 0.985
                found = True
                foundCount +=1
                matched_osm_id = oldFeature['properties']['@id']
                if dtp_osm_id != "undefined":
                    if dtp_osm_id != matched_osm_id:
                        mismatched_osm_ids.append(newFeature['properties']['dtp_url'])
                    else:
                        dtp_id = newFeature['properties']['dtp_url'].replace('https://content.digitizetheplanet.org/rules/show_protectedarea/', '')
                        mapping_table.append(f"{matched_osm_id};{dtp_id}")
                sameFeatures.append(newFeature)
        if not found:
            newCount += 1
            newFeaturesOut.append(newFeature)

if len(mismatched_osm_ids) > 0:
    print("Mismatched Areas:")
    print("\n".join(mismatched_osm_ids))

with open(mappingFile, 'w') as f:
    f.write("\n".join(mapping_table))

print(f"Gefundene Gebiete = {foundCount} -> mapping in {mappingFile}")
print(f"Neue/Geänderte Gebiete = {newCount} -> in {newAreasFile}")

# --- 22.05.2023 13:13:36 ---
# Gefundene Gebiete = 438
# Neue/Geänderte Gebiete = 30 -> in ./areas/new-areas.geojson

with fiona.open(newAreasFile, 'w', encoding='utf-8', crs={'init':'epsg:4326'}, driver='GeoJSON', schema=schema) as out:
    for f in newFeaturesOut:
        out.write(f)

schema['properties'] = {k: v for k, v in schema['properties'].items() if k in ['name', 'boundary']}
with fiona.open(newAreasFileJosm, 'w', encoding='utf-8', crs={'init':'epsg:4326'}, driver='GeoJSON', schema=schema) as out:
    for f in newFeaturesOut:
        f['properties'] = {k: v for k, v in f['properties'].items() if k in ['name', 'boundary']}
        out.write(f)