import requests
import osmnx as ox
import json
import time
import os

# --- Configuration ---
# NUST H-12 Center Coordinates
CENTER_LAT = 33.6425
CENTER_LON = 72.9930
RADIUS = 1500  # Meters

# Files
RAW_MAP_FILE = "nust_raw.osm" # The raw XML from OpenStreetMap
NODES_FILE = "nodes.json"
EDGES_FILE = "edges.json"
ELEVATION_API = "https://api.open-elevation.com/api/v1/lookup"

def download_raw_map_data():
    """
    Step 1: Download raw XML directly from Overpass API.
    Reference: https://wiki.openstreetmap.org/wiki/Overpass_API
    """
    print(f"[1/4] Downloading Raw OSM Data (Direct API Strategy)...")
    
    # Overpass Query Language (QL)
    # This asks for all "ways" (roads) with a "highway" tag within RADIUS of CENTER
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:xml];
    (
      way["highway"](around:{RADIUS},{CENTER_LAT},{CENTER_LON});
    );
    (._;>;);
    out meta;
    """
    
    try:
        # We use a stream download to handle large files without memory crashes
        response = requests.get(overpass_url, params={'data': overpass_query}, stream=True, timeout=60)
        
        if response.status_code == 200:
            with open(RAW_MAP_FILE, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"      Success! Saved raw map to '{RAW_MAP_FILE}'")
            return True
        else:
            print(f"      Error: Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"      Critical Network Error: {e}")
        return False

def process_graph_locally():
    """
    Step 2: Use osmnx to parse the LOCALLY saved file.
    """
    print(f"[2/4] Processing local XML file into Graph...")
    
    if not os.path.exists(RAW_MAP_FILE):
        raise FileNotFoundError("Raw map file not found. Download failed.")

    # Load graph from the XML file
    G = ox.graph_from_xml(RAW_MAP_FILE)
    
    # ERROR FIX: Wrap simplification in try-except
    # If the graph is already simple, osmnx throws an error. We catch it and move on.
    try:
        G = ox.simplify_graph(G)
        print("      Simplification successful.")
    except Exception:
        print("      Graph was already simplified. Skipping optimization step.")
    
    print(f"      Graph built! Nodes: {len(G.nodes)}, Edges: {len(G.edges)}")
    return G
def fetch_elevation_safe(node_list):
    """
    Safe batch fetcher for elevation
    """
    try:
        resp = requests.post(ELEVATION_API, json={"locations": node_list}, timeout=15)
        if resp.status_code == 200:
            return resp.json()['results']
    except:
        pass
    return None

def build_database(G):
    print("[3/4] Enriching Elevation & Cleaning Edges...")
    
    nodes_export = {}
    edges_export = []
    
    # 1. Prepare Nodes
    all_nodes = []
    node_ids = []
    
    for n_id, data in G.nodes(data=True):
        nodes_export[n_id] = {
            "id": n_id,
            "lat": data['y'],
            "lon": data['x'],
            "elevation": 508 # Default NUST height
        }
        all_nodes.append({"latitude": data['y'], "longitude": data['x']})
        node_ids.append(n_id)

    # 2. Fetch Elevation (Batch of 100)
    # Only doing first 200 nodes to save time/bandwidth for this demo.
    # In production, you would loop all.
    print("      (Fetching elevation for a subset of nodes to speed up)...")
    subset = all_nodes[:200] 
    results = fetch_elevation_safe(subset)
    
    if results:
        for i, res in enumerate(results):
            real_id = node_ids[i]
            nodes_export[real_id]['elevation'] = res['elevation']
        print(f"      Updated elevation for {len(results)} nodes.")

    # 3. Process Edges
    for u, v, data in G.edges(data=True):
        hw = data.get('highway', '')
        
        # Multi-modal logic
        is_walk = True
        is_car = True
        
        if hw in ['footway', 'path', 'steps']: is_car = False
        if hw in ['motorway']: is_walk = False
        
        # Handle OSM list weirdness
        length = data.get('length', 0)
        if isinstance(length, list): length = float(length[0])
        
        edges_export.append({
            "u": u,
            "v": v,
            "weight": float(length),
            "is_walkable": is_walk,
            "is_drivable": is_car,
            "name": data.get('name', "Unknown")
        })

    return nodes_export, edges_export

def save_data(nodes, edges):
    print(f"[4/4] Saving JSON database...")
    with open(NODES_FILE, 'w') as f: json.dump(nodes, f, indent=2)
    with open(EDGES_FILE, 'w') as f: json.dump(edges, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    # Pipeline Execution
    if download_raw_map_data():
        G = process_graph_locally()
        nodes, edges = build_database(G)
        save_data(nodes, edges)
    else:
        print("Pipeline aborted.")