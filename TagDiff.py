import json, re, requests, sys, os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# produced by DTPAreas2GeoJson.py
with open('./geojson/cat_18-19.geojson') as f:
  dtp = json.load(f)

osm_file = './Schongebiete.geojson'
response = requests.get('https://www.xctrails.org/osm/Schongebiete.geojson')
if response.status_code == 200:
    with open(osm_file, 'wb') as file:
        file.write(response.content)
else:
    print(f"Failed to download file: {response.status_code}")
    sys.exit(1)

with open(osm_file) as f:
  osm = json.load(f)

def format_osm_access(access):
    access = re.sub(r'([a-z])(\d)', r'\1 \2', access)
    access = re.sub(r'(\d)-([A-Z])', r'\1 - \2', access)
    access = re.sub(r'(\d)- ([A-Z])', r'\1 - \2', access)
    access = re.sub(r'([a-zA-Z]) (\d) ', r'\1 0\2 ', access)
    access = re.sub(r'([a-z]) - ', r'\1 01 - ', access)
    access = re.sub(r'Mar\)', 'Mar 31)', access)
    access = re.sub(r'Apr\)', 'Apr 30)', access)
    access = re.sub(r'May\)', 'May 31)', access)

    access = re.sub(r'no@', 'no @', access)

    return access

def get_props_byid(data, id):
    for f in data['features']:
        if f['properties']['@id'] == id:
            if 'access:conditional' in f['properties']:
                f['properties']['access:conditional'] = format_osm_access(f['properties']['access:conditional'])
            if 'access:onroad:conditional' in f['properties']:
                f['properties']['access:onroad:conditional'] = format_osm_access(f['properties']['access:onroad:conditional'])
            if 'access:offroad:conditional' in f['properties']:
                f['properties']['access:offroad:conditional'] = format_osm_access(f['properties']['access:offroad:conditional'])
            return f['properties']
    return None

diffs = []
not_founds = []

for f in dtp['features']:
    osm_id = f['properties']['osm_id'].replace('https://www.openstreetmap.org/', '')
    if osm_id == 'undefined':
        continue;
    if osm_id == 'way/923695934':
        # FIXME: Siebenhütten no @ (Dec-Mar 12:00-08:00)
        # manueller check: passt
        continue
    # if osm_id == 'way/1146904216':
    #     print(osm_id)
    osm_props = get_props_byid(osm, osm_id)
    # FIXME: there are a couple of protect_class=4/7 areas in DTP cat 18/19 which are not in Schongebiete.json
    if osm_props == None:
        not_founds.append({'dtp_url': f['properties']['dtp_url'], 'name': f['properties']['name'], 'osm_id': osm_id})
        continue;
    
    if not 'access' in osm_props: osm_props['access'] = '';
    if not 'access:conditional' in osm_props: osm_props['access:conditional'] = '';
    if not 'seasonal' in osm_props: osm_props['seasonal'] = '';

    for dtp_access in f['properties']['dtp_access']:
        dtp_access = dtp_access.replace(' [Entering the area]', '')
        if dtp_access.startswith('access:conditional=') or dtp_access.startswith('access:onroad:conditional=') or dtp_access.startswith('access:offroad:conditional='):
                rule = dtp_access.split('=')[1]
                if rule == osm_props['access:conditional']:
                    continue
                if 'access:onroad:conditional' in osm_props and rule == osm_props['access:onroad:conditional']:
                    continue
                if 'access:offroad:conditional' in osm_props and rule == osm_props['access:offroad:conditional']:
                    continue
        
        if dtp_access == 'access=no' and osm_props['access'] == 'no':
            continue

        if dtp_access == 'access:offroad=no' and 'access:offroad' in osm_props and osm_props['access:offroad'] == 'no':
            continue

        if dtp_access == 'access:conditional=discouraged @ (Dec 01 - Apr 30)':
            if osm_props['access'] == 'discouraged' and osm_props['seasonal'] == 'winter':
                continue
        elif dtp_access == 'access:conditional=no @ (Dec 01 - Apr 30)':
            if osm_props['access'] == 'no' and osm_props['seasonal'] == 'winter':
                continue
        elif dtp_access == 'access=no':
            if osm_props['access'] == 'no' and ( osm_props['seasonal'] == 'no' or osm_props['seasonal'] == 'undefined' ):
                continue

        dtp_access_c = ''
        if dtp_access:
            access_kind = ''
            if 'offroad' in dtp_access:
                access_kind = 'offroad '
            if 'onroad' in dtp_access:
                access_kind = 'onroad '
            if dtp_access.startswith('access:'):
                dtp_access_c = access_kind + dtp_access.split('=')[1]
                dtp_access = ''
            else:
                dtp_access = access_kind + dtp_access.split('=')[1]
                dtp_access_c = ''
                
        osm_access_c = osm_props['access:conditional']
        if 'access:onroad:conditional' in osm_props:
            osm_access_c = "onroad " + osm_props['access:onroad:conditional']
        elif 'access:offroad:conditional' in osm_props:
            osm_access_c = "offroad " + osm_props['access:offroad:conditional']

        if dtp_access_c == osm_access_c:
            continue

        diffs.append({'osm_id': osm_id, 'dtp_url': f['properties']['dtp_url'], 'name': f['properties']['name'], 
                    'district': f['properties']['district'], 'dtp_access': dtp_access, 'dtp_access_c': dtp_access_c,
                    'osm_access': osm_props['access'], 'osm_access_c': osm_access_c, 'osm_seasonal': osm_props['seasonal']})

# filterd_diffs = []
# for diff in diffs:
#     if diff['district'] == 'Bregenz':
#         filterd_diffs.append(diff)
# diffs = filterd_diffs

print(len(diffs))

environment = Environment(loader=FileSystemLoader("./templates/"))
template = environment.get_template("tagdiff_report.html")
if not os.path.exists("./reports"): os.mkdir("./reports")
with open('./reports/tagdiff_report.html', mode="w", encoding="utf-8") as results:
    results.write(template.render({
        'generated_at': datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        'count': len(diffs),
        'diffs': diffs,
        'not_founds': not_founds
    }))

# input for JOSM script generation
# with open('./output/osm_patch_ids.txt', mode="w", encoding="utf-8") as results:
#     for diff in diffs:
#         if diff['district'] == 'Bregenz' and diff['dtp_access_c'] == 'discouraged @ (Dec 01 - Apr 30)':
#             results.write(diff['osm_id']+'\n')
