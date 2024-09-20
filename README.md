# Overview
A selection of scripts to download WWSG data from the [DTP API](https://content.digitizetheplanet.org/de/api/dokumentation/) and DAV API (work in progress) for JOSM import/update preparation

As usual: 
```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Output and results are provided as examples, based on DTP and OSM data as of Sep 20, 2024

# Procedures
Note: There is no sanity checking for missing dependecies, etc. !

## DTPAreas2GeoJson.py
Extracts all cat=x geometries from DTP endpoint and produces, supports caching of DTP data to speed up runs during code tweaking
Runs for a couple of minutes unless rebuild_cache = False

### Outputs:
- ./geojson/cat_18-19.geojson (mostly german alps)
- ./geojson/cat_20-41.geojson (mostly austrian alps)

### Import to geoserver (on xctrails.org):
```
ogr2ogr -f "PostgreSQL" PG:"dbname=schongebiete user=postgres" ./cat_18-19.geojson -nln dtp_18_19 -overwrite
```
-> https://www.xctrails.org/schongebiete/SchongebieteWMSLayer.html

## GeoJsonAreaDiff.py
Compares OSM Schongebiete geometry with new geometry (from DTP)

### Inputs:
- ./geojson/cat_18-19.geojson
- https://www.xctrails.org/osm/Schongebiete.geojson (downloaded in script, 1:1 from cat_18-19.geojson)

### Output:
- output/new-areas-josm.geojson as input for JOSM updates (don't re-copy DTP attributes into OSM in that case!)
  - shape import/merges in JOSM: see https://www.xctrails.org/videos/JOSM-Shape-Korrektur.mp4
- output/new-areas.geojson with all properties (possibly for new imports - manually check all tags in JOSM !!!)
- osm2dtp_mapping.csv - as input for GenerateJosmScript-DTP_ID.py (only used once)

## IdMappingReport.py
DTP -> OSM Category 18/19 mapping status report
removed and missing areas based on osm_id in DTP data

### Inputs:
- cached DTP data
- live/cached OSM data

### Outputs:
- ./reports/dtp2osm_report.html
- ./reports/dtp2osm_report.csv"

## TagDiff.py

### Inputs:
- ./geojson/cat_18-19.geojson - from DTPAreas2GeoJson.py
- https://www.xctrails.org/osm/Schongebiete.geojson (downloaded in script)

### Outputs:
- ./reports/tagdiff_report.html
