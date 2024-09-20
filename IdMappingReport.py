import os
from datetime import datetime
from tinydb import TinyDB, Query
from OSMPythonTools.api import Api
from OSMPythonTools.cachingStrategy import CachingStrategy, JSON
from jinja2 import Environment, FileSystemLoader
from tqdm import tqdm
import logging
logging.getLogger("OSMPythonTools").setLevel(logging.CRITICAL)

from dtp import *

CachingStrategy.use(JSON, cacheDir="./cache/osm")

# FIXME: test that from scratch
# rebuild_cache doesn't reload individual areas unless the cache dir is manuelly cleaned!
rebuild_cache = False
if not os.path.exists(dtp_cache_dir):
    os.mkdir(dtp_cache_dir)
    rebuild_cache = True

if not os.path.exists("./reports"): os.mkdir("./reports")
report_filename = "./reports/dtp2osm_report.html"
csv_filename = "./reports/dtp2osm_report.csv"

generated_at = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def query_data(cat_id):
    removed_in_osm = []
    not_in_osm = []
    api = Api()
    db = TinyDB(areas_db_file)
    q = Query()
    areas = db.search(q.category.id == cat_id)
    print(f"Found {len(areas)} cat {cat_id} areas...")

    with tqdm(total=len(areas)) as pbar:
        for area in areas:
            pbar.update(1)
            osm_id = area["osm_id"]
            full_area = get_dtp_area_by_id(area["uuid"], rebuild_cache)
            area["centroid"] = { "lat": full_area["centroid"]["coordinates"][1], "lon": full_area["centroid"]["coordinates"][0] }
            if osm_id != None:
                try:
                    # print(f"checking {osm_id} ...")
                    osm_object = api.query(osm_id) # when is the ./cache updated - apparently daily ...
                    if not osm_object:
                        removed_in_osm.append(area)
                except:
                    removed_in_osm.append(area)
            else:
                not_in_osm.append(area)

    print(f"Found {len(removed_in_osm)} removed areas...")
    print(f"Found {len(not_in_osm)} missing areas...")

    return removed_in_osm, not_in_osm

load_dtp_areas(rebuild_cache)

removed_in_osm_18, not_in_osm_18 = query_data(18)
removed_in_osm_19, not_in_osm_19 = query_data(19)
# removed_in_osm_20, not_in_osm_20 = query_data(20)
# removed_in_osm_41, not_in_osm_41 = query_data(41)

environment = Environment(loader=FileSystemLoader("./templates/"))
template = environment.get_template("area_report.html")
with open(report_filename, mode="w", encoding="utf-8") as results:
    results.write(template.render({
        "generated_at": generated_at,
        "removed_in_osm_18": removed_in_osm_18,
        "not_in_osm_18": not_in_osm_18,
        "removed_in_osm_19": removed_in_osm_19,
        "not_in_osm_19": not_in_osm_19,
        # "removed_in_osm_20": removed_in_osm_20,
        # "not_in_osm_20": not_in_osm_20,
        # "removed_in_osm_41": removed_in_osm_41,
        # "not_in_osm_41": not_in_osm_41,
    }))

def xc_url(area):
    return f"https://www.xctrails.org/schongebiete/SchongebieteWMSLayer.html?lat={area['centroid']['lat']}&lon={area['centroid']['lon']}"

with open(csv_filename, mode="w", encoding="utf-8") as csv:
    for area in removed_in_osm_18:
        csv.write(f"18;wrong_osm_id;{area['name_de']};{area['dtp_url']};{xc_url(area)}\n")
    for area in not_in_osm_18:
        csv.write(f"18;missing_osm_id;{area['name_de']};{area['dtp_url']};{xc_url(area)}\n")
    for area in removed_in_osm_19:
        csv.write(f"19;wrong_osm_id;{area['name_de']};{area['dtp_url']};{xc_url(area)}\n")
    for area in not_in_osm_19:
        csv.write(f"19;missing_osm_id;{area['name_de']};{area['dtp_url']};{xc_url(area)}\n")
