import os
from geojson import FeatureCollection, Feature, Polygon, MultiPolygon
import geojson
from tinydb import TinyDB, Query
from tqdm import tqdm
import datetime

import logging
logging.getLogger("OSMPythonTools").setLevel(logging.CRITICAL)

from dtp import *

out_dir = "./geojson"
if not os.path.exists(out_dir): os.mkdir(out_dir)

rebuild_cache = True # set to False to use cached DTP data (for development...)

# ogr2ogr -f "PostgreSQL" PG:"dbname=schongebiete user=postgres" ./cat_18-19.geojson -nln dtp_18_19 -overwrite
# ogr2ogr -f "PostgreSQL" PG:"dbname=schongebiete user=postgres" ./cat_20-41.geojson -nln dtp_20_41 -overwrite

load_dtp_areas(rebuild_cache)

activities = set()
activity_places = set()
permissions = set()
seasons = set()

def date2osm(d):
    if d != None:
        y, m, d = d.split('-')
        month_name = datetime.datetime(1, int(m), 1).strftime("%b")
        return f'{month_name} {d}'

def translate_dtp_rules(area_detail):
    access_list = []

    for rules in area_detail['rules']:
    
        activity = rules['activity']['activity'] # Entering the area, Entering off the beaten path, Hiking, Dogs
        activities.add(activity)

        activity_place = rules['activityplace']['place'] # Total area of the territory
        activity_places.add(activity_place) 

        permission = rules['activitypermission']['permission_en'] # discouraged, forbidden
        if permission == 'forbidden':
            permission = 'no'
        permissions.add(permission)

        if 'season' in rules and rules['season']: 
            season = rules['season']['season_en']
            seasons.add(season)

        season_start = date2osm(rules['season_start'])
        season_end = date2osm(rules['season_end'])

        access = ''
        if activity == "Entering the area" or activity == "Hiking" or activity == "Winter sport":
            if season_start != None and season_end != None:
                access = f'access:conditional={permission} @ ({season_start} - {season_end}) [{activity}]'
            else:
                access = f'access={permission}'
        elif activity == "Entering off the beaten path":
            if season_start != None and season_end != None:
                access = f'access:offroad:conditional={permission} @ ({season_start} - {season_end})'
            else:
                access = f'access:offroad={permission}'

        access_list.append(access)

    return access_list


# export dtp detailed areas
def export_areas(cat_id):
    db = TinyDB(areas_db_file)
    q = Query()
    areas = db.search(q.category.id == cat_id)
    print(f"Found {len(areas)} cat {cat_id} areas, reading individual areas...")
    multi_polygons = []

    with tqdm(total=len(areas)) as pbar:
        for area in areas:
            pbar.update(1)

            uuid = area["uuid"]
            area_detail = get_dtp_area_by_id(uuid, rebuild_cache)
            if not "geometry" in area_detail or area_detail["geometry"] == None or not "coordinates" in area_detail["geometry"]:
                continue
            
            coords = area_detail["geometry"]["coordinates"]
            mps = []
            for coord in coords:
                lls = []
                for ll in coord:
                    lls.append(ll)
                mps.append(lls)

            osm_url = ""
            if area_detail["osm_id"]:
                osm_url = "https://www.openstreetmap.org/" + area_detail["osm_id"]
            else:
                osm_url = "undefined"

            district = ""
            if len(area_detail["districts"]): district = area_detail["districts"][0]["name_2"]
            props = { "name": area_detail["name"], "district": district, 
                        "boundary": "protected_area", "dtp_url": area_detail["dtp_url"], "osm_id": osm_url}
            rules = translate_dtp_rules(area_detail)
            props['dtp_access'] = rules
            # b/c geoserver's freemarker template insists on treating this as string even if it's a string[] :-(((
            props['dtp_access_str'] = ";".join(rules)

            if len(mps) > 1:
                multi_polygons.append(f'Multipolygon {area_detail["name"]} {area_detail["dtp_url"]}')
                all_features.append(Feature(geometry=MultiPolygon(mps),properties=props))
            else:
                all_features.append(Feature(geometry=Polygon(mps[0]),properties=props))
            if osm_url != "undefined":
                mapping_table.append(f"{osm_url};{area_detail['uuid']}")

    if len(multi_polygons) > 0:
        print("Multipolygons: ")
        print("\n".join(multi_polygons))

def dump_files(cats):
    with open(f'{out_dir}/{cats}.geojson', 'w') as f:
        geojson.dump(FeatureCollection(all_features), f)

    with open(f'{out_dir}/{cats}_mapping.csv', 'w') as f:
        f.write("\n".join(mapping_table))

# modified by export_areas ! reset if necessary
all_features = []
mapping_table = []
export_areas(18)
export_areas(19)
dump_files("cat_18-19")

all_features = []
mapping_table = []
cats = "cat_20-41"
export_areas(20)
export_areas(41)
dump_files("cat_20-41")

# Geigelstein is cat 2 !!!
# all_features = []
# mapping_table = []
# export_areas(2)
# dump_files("cat_2")
# props = { "name": area_detail["name"], "district": area_detail["districts"][0]["name_2"],
#                                                    ~~~~~~~~~~~~~~~~~~~~~~~~^^^

# print("activities")
# for activity in activities: print(activity)
# print("activity_places")
# for activity_place in activity_places: print(activity_place)
# print("permissions")
# for permission in permissions: print(permission)
# print("seasons")
# for season in seasons: print(season)
