import requests
import osmnx as ox
import json
import os
import xml.etree.ElementTree as ET
from shapely.geometry import mapping
import time

# --- Configuration ---
CENTER_LAT = 33.6425
CENTER_LON = 72.9930
RADIUS = 2000 

# Files
RAW_MAP_FILE = "nust_raw.osm"
NODES_FILE = "nodes.json"
EDGES_FILE = "edges.json"
POIS_FILE = "pois.json"
ELEVATION_API = "https://api.open-elevation.com/api/v1/lookup"

def download_raw_map_data():
    print(f"[1/5] Downloading Real-World Map Data...")
    
    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    # Query: Get everything with a name OR a barrier (Gates)
    overpass_query = f"""
    [out:xml][timeout:90];
    (
      way["highway"](around:{RADIUS},{CENTER_LAT},{CENTER_LON});
      node["name"](around:{RADIUS},{CENTER_LAT},{CENTER_LON});
      node["barrier"](around:{RADIUS},{CENTER_LAT},{CENTER_LON}); 
      way["name"](around:{RADIUS},{CENTER_LAT},{CENTER_LON});
    );
    (._;>;);
    out meta;
    """
    
    for url in servers:
        try:
            print(f"      Trying server: {url} ...")
            response = requests.get(url, params={'data': overpass_query}, stream=True, timeout=90)
            if response.status_code == 200:
                with open(RAW_MAP_FILE, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk: f.write(chunk)
                print(f"      Success! Saved raw map to '{RAW_MAP_FILE}'")
                return True
        except Exception as e:
            print(f"      Connection failed: {e}")
    return False

def process_graph_locally():
    print(f"[2/5] Building Road Network (Graph)...")
    if not os.path.exists(RAW_MAP_FILE):
        raise FileNotFoundError("Raw map file not found.")
    
    # 1. Load Graph
    G = ox.graph_from_xml(RAW_MAP_FILE)
    
    # 2. CRITICAL: DO NOT SIMPLIFY "BARRIER" NODES
    # Simplifying removes the "Gate" node because it's just a dot on a line.
    # We skip simplification to keep the exact gate locations.
    print("      Skipping simplification to preserve Gate nodes...")
    
    return G

def extract_pois_from_xml():
    print(f"[3/5] Extracting POIs from OSM Tags...")
    pois = []
    try:
        tree = ET.parse(RAW_MAP_FILE)
        root = tree.getroot()
        
        for node in root.findall('node'):
            tags = {tag.get('k'): tag.get('v') for tag in node.findall('tag')}
            
            name = tags.get('name')
            barrier = tags.get('barrier')
            amenity = tags.get('amenity')
            
            # Intelligent Naming
            final_name = name
            poi_type = "Location"

            if barrier in ['gate', 'entrance', 'toll_booth']:
                poi_type = "Entrance"
                if not final_name: final_name = f"Gate ({node.get('id')})"
            
            if amenity: poi_type = amenity

            if final_name:
                pois.append({
                    "name": final_name,
                    "lat": float(node.get('lat')),
                    "lon": float(node.get('lon')),
                    "type": poi_type
                })
    except Exception as e:
        print(f"      Warning: XML parsing issue ({e}).")

    print(f"      Found {len(pois)} POIs.")
    return pois

def build_database(G):
    print("[4/5] Processing Topology & Elevation...")
    nodes_export = {}
    edges_export = []
    
    node_ids = []
    api_payload = []
    
    # Nodes
    for n_id, data in G.nodes(data=True):
        nodes_export[n_id] = {
            "id": n_id,
            "lat": data['y'],
            "lon": data['x'],
            "elevation": 508
        }
        node_ids.append(n_id)
        api_payload.append({"latitude": data['y'], "longitude": data['x']})

    # Elevation (Sample limited for speed)
    subset = api_payload[:300] 
    try:
        resp = requests.post(ELEVATION_API, json={"locations": subset}, timeout=5)
        if resp.status_code == 200:
            for i, res in enumerate(resp.json()['results']):
                nodes_export[node_ids[i]]['elevation'] = res['elevation']
    except: pass

    # Edges
    for u, v, data in G.edges(data=True):
        hw = data.get('highway', '')
        
        # --- SMART CLASSIFICATION ---
        is_walk = True
        is_car = True
        
        # Motorways are for cars only
        if hw in ['motorway', 'motorway_link', 'trunk', 'trunk_link']:
            is_walk = False
        
        # Paths are for walking only
        if hw in ['footway', 'path', 'steps', 'pedestrian']:
            is_car = False
            
        # Service roads (Campus) are BOTH
        if hw in ['service', 'residential', 'unclassified']:
            is_car = True
            is_walk = True

        length = float(data.get('length', 0)) if not isinstance(data.get('length'), list) else float(data.get('length')[0])
        
        # Save the highway type so we can use it in structures.py
        edges_export.append({
            "u": u, "v": v, "weight": length,
            "is_walkable": is_walk, "is_drivable": is_car,
            "highway": hw, # <--- NEW FIELD
            "geometry": [] # Simplified for this snippet
        })

    return nodes_export, edges_export

def save_data(nodes, edges, pois):
    print(f"[5/5] Saving Database...")
    with open(NODES_FILE, 'w') as f: json.dump(nodes, f, indent=2)
    with open(EDGES_FILE, 'w') as f: json.dump(edges, f, indent=2)
    with open(POIS_FILE, 'w') as f: json.dump(pois, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    if download_raw_map_data():
        G = process_graph_locally()
        pois = extract_pois_from_xml()
        nodes, edges = build_database(G)
        save_data(nodes, edges, pois)
    else:
        print("Pipeline Aborted.")