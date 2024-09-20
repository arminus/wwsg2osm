# provided by the DAV cartography team

import requests
import geopandas as gpd
import json
import os

# URL des Feature Layers
layer_url = "https://services-eu1.arcgis.com/7LJj397HSK8DGWBQ/arcgis/rest/services/2024_Schutzgebiete_Simon_DTP/FeatureServer/0/query"

# Token - read this token from a file called .dav-token
# Note: expires all 14 days
token_file_path = '.dav-token'
if os.path.exists(token_file_path):
    with open(token_file_path, 'r') as token_file:
        token = token_file.read().strip()
else:
    raise FileNotFoundError(f"Token file not found: {token_file_path}")

# Pfade zur Speicherung der Dateien
if not os.path.exists('./dav'): os.mkdir('./dav')
geojson_file_path = './dav/DAV_Schutzgebiete.geojson'

# Parameter für die Abfrage
params = {
    'where': '1=1',  # Abfragebedingung (hier: alle Features)
    'outFields': '*',  # Alle Felder abrufen
    'f': 'geojson',  # Format der Antwort als GeoJSON
    'token': token  # Dein Token
}

# Anfrage an den API-Endpunkt senden
response = requests.get(layer_url, params=params)

# Überprüfen, ob die Anfrage erfolgreich war
if response.status_code == 200:
    try:
        # Versuchen, die GeoJSON-Daten zu parsen
        geojson_data = response.json()

        # Überprüfen, ob die GeoJSON-Daten korrekt sind
        if 'features' in geojson_data and len(geojson_data['features']) > 0:
            # Speichern der GeoJSON-Daten
            with open(geojson_file_path, 'w') as file:
                json.dump(geojson_data, file)
            print(f"Die GeoJSON-Datei wurde erfolgreich in {geojson_file_path} gespeichert.")
            
            # GeoJSON-Datei in ein GeoDataFrame laden
            gdf = gpd.read_file(geojson_file_path)

            # Überprüfen, ob das GeoDataFrame leer ist
            # if gdf.empty:
            #     print("Das GeoDataFrame ist leer.")
            # else:
            #     # In Shapefile umwandeln und speichern
            #     gdf.to_file(shapefile_path, driver='ESRI Shapefile')
            #     print(f"Das Shapefile wurde erfolgreich in {shapefile_path} gespeichert.")
        else:
            print("Die GeoJSON-Daten enthalten keine Features.")
    except json.JSONDecodeError:
        print("Fehler beim Parsen der GeoJSON-Daten.")
else:
    print(f"Fehler bei der Anfrage: {response.status_code} - {response.text}")
    
#FIXME: 2m north-west offset relative to the DTP data - why ?
#TODO: translate DAV attributes to OSM tags (similar to DTPAreas2GeoJson.py:translate_dtp_rules)
