import osmnx as ox
import networkx as nx
import json
import googlemaps
import os
import time

# ================= CONFIGURATION =================
# Your Google Maps API Key
GOOGLE_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY" 

# Islamabad Coverage - Multiple areas to cover more ground
# Center point between NUST and major Islamabad areas
LOCATION_POINT = (33.6800, 73.0300)  # Shifted to cover more of Islamabad
DIST_RADIUS = 8000  # 8km radius - covers NUST, F-sectors, G-sectors, I-sectors

# File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
NODES_FILE = os.path.join(DATA_DIR, "nodes.json")
EDGES_FILE = os.path.join(DATA_DIR, "edges.json")
POIS_FILE = os.path.join(DATA_DIR, "pois.json")

def build_nust_database():
    print("🚀 STARTING DATA PIPELINE (Google Hybrid Engine)...")
    
    # 1. Initialize Google Client
    try:
        gmaps = googlemaps.Client(key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"❌ Error initializing Google Client: {e}")
        return

    # 2. Get Road Network (Topology)
    print("[1/4] Downloading Road Network (OSM)...")
    # We use 'all' to get both walking paths and driving roads
    G = ox.graph_from_point(LOCATION_POINT, dist=DIST_RADIUS, network_type='all', simplify=True)
    print(f"      Graph created: {len(G.nodes)} nodes, {len(G.edges)} edges.")
    
    # 3. Inject Google Elevation Data
    print("[2/4] Fetching Precise Elevation (Google Cloud)...")
    nodes = list(G.nodes(data=True))
    coords = [(data['y'], data['x']) for _, data in nodes]
    elevation_results = []
    
    # Google limits to 512 locations per request
    batch_size = 400 
    for i in range(0, len(coords), batch_size):
        batch = coords[i : i + batch_size]
        print(f"      Requesting batch {i//batch_size + 1}...")
        try:
            results = gmaps.elevation(batch) 
            elevation_results.extend(results)
            time.sleep(0.1) 
        except Exception as e:
            print(f"      ❌ API Error in batch: {e}")
            elevation_results.extend([{'elevation': 0}] * len(batch))
            
    # Map elevation back to nodes
    node_ids = [n[0] for n in nodes]
    for i, node_id in enumerate(node_ids):
        if i < len(elevation_results):
            G.nodes[node_id]['elevation'] = elevation_results[i]['elevation']
        else:
            G.nodes[node_id]['elevation'] = 0.0

    # 4. Extract POIs
    print("[3/4] Extracting POIs...")
    tags = {
        'amenity': ['cafe', 'fast_food', 'fuel', 'library', 'university', 'parking', 'restaurant'],
        'building': ['university', 'dormitory', 'residential', 'commercial'],
        'barrier': ['gate']
    }
    
    try:
        pois_gdf = ox.features_from_point(LOCATION_POINT, tags=tags, dist=DIST_RADIUS)
        poi_list = []
        for _, row in pois_gdf.iterrows():
            if 'name' in row and str(row['name']) != 'nan':
                pt = row.geometry.centroid
                poi_list.append({
                    "name": row['name'],
                    "lat": pt.y,
                    "lon": pt.x,
                    "type": row.get('amenity', row.get('building', 'poi'))
                })
    except Exception as e:
        print(f"      Warning: POI extraction skipped ({e})")
        poi_list = []

    # 5. Save to JSON (Formatting for YOUR structures.py)
    print("[4/4] Saving Database...")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # --- SAVE NODES ---
    nodes_data = {}
    for u, d in G.nodes(data=True):
        nodes_data[str(u)] = {
            "lat": d['y'],
            "lon": d['x'],
            "elevation": d.get('elevation', 0)
        }
    
    # --- SAVE EDGES (The Fix) ---
    edges_data = []
    for u, v, d in G.edges(data=True):
        hw = d.get('highway', 'road')
        if isinstance(hw, list): hw = hw[0] # Handle list types
        
        # LOGIC: Determine Walkable vs Drivable based on tag
        # This logic aligns with what CityGraph expects
        is_walkable = True 
        is_drivable = True
        
        # Non-drivable things
        if hw in ['footway', 'steps', 'corridor', 'path', 'cycleway', 'pedestrian', 'track']:
            is_drivable = False
            
        # Non-walkable things (Highways mostly)
        if hw in ['motorway', 'motorway_link']:
            is_walkable = False
            
        edges_data.append({
            "u": str(u), 
            "v": str(v),
            "weight": d.get('length', 0),  # RENAMED: length -> weight
            "is_walkable": is_walkable,    # ADDED
            "is_drivable": is_drivable,    # ADDED
            "highway": hw,
            "geometry": str(d.get('geometry', '')) 
        })

    with open(NODES_FILE, 'w') as f: json.dump(nodes_data, f)
    with open(EDGES_FILE, 'w') as f: json.dump(edges_data, f)
    with open(POIS_FILE, 'w') as f: json.dump(poi_list, f)

    print("\n✅ SUCCESS: Database rebuilt perfectly for structures.py!")

if __name__ == "__main__":
    build_nust_database()