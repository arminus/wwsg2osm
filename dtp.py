import requests, os, json
from tinydb import TinyDB
from tqdm import tqdm

dtp_cache_dir = "./cache/dtp"
areas_db_file = f"{dtp_cache_dir}/dtp_areas.json"

def get_dtp_area_by_id(id, rebuild_cache=False):
    cache_file = f"{dtp_cache_dir}/{id}"
    if os.path.exists(cache_file) and not rebuild_cache:
        with open(cache_file, encoding="utf-8") as f:
            return json.load(f)
    else:
        url = f"https://content.digitizetheplanet.org/api/protectedarea/{id}"
        response = requests.get(url).json();
        with open(cache_file, mode="w", encoding="utf-8") as f:
            f.write(json.dumps(response, indent=2))
        return response

def load_dtp_areas(rebuild_cache=False):
    if not os.path.exists(dtp_cache_dir): os.makedirs(dtp_cache_dir)
    if rebuild_cache and os.path.exists(areas_db_file):
        os.remove(areas_db_file)
    
    if not os.path.exists(areas_db_file):
        db = TinyDB(areas_db_file)
        print("Loading DTP areas...")
        url = "https://content.digitizetheplanet.org/api/protectedarea/?page=1"
        response = requests.get(url).json()
        count = response["count"]
        db.insert_multiple(response["results"])
        with tqdm(total=count) as pbar:
            pbar.update(50)
            while "next" in response and response["next"] != None:
                url = response["next"]
                response = requests.get(url).json()
                db.insert_multiple(response["results"])
                pbar.update(50)

