from structures import CityGraph
from algorithms import a_star_search
from visualizer import generate_map  # <--- CHANGE 1

def get_user_selection(pois_list, prompt_text):
    # ... (Same as before) ...
    while True:
        print(f"\n--- {prompt_text} ---")
        query = input("Search Location (e.g., 'Cafe', 'Library', 'Gate'): ").lower().strip()
        matches = [p for p in pois_list if query in p['name'].lower()]
        if not matches:
            print("No matches found. Try again.")
            continue
        print(f"Found {len(matches)} matches:")
        for i, p in enumerate(matches[:5]):
            print(f"  {i+1}. {p['name']} ({p['type']})")
        try:
            choice = int(input("Select number (0 to search again): "))
            if choice == 0: continue
            if 1 <= choice <= len(matches):
                selected = matches[choice-1]
                return selected['lat'], selected['lon'], selected['name']
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter a number.")

def calculate_stats(graph, path):
    total_climb = 0
    total_descent = 0
    for i in range(len(path) - 1):
        u = graph.nodes[path[i]]
        v = graph.nodes[path[i+1]]
        
        # <--- CHANGE 2: Handle 'elevation' key from new pipeline
        ele_u = u.get('elevation', 0)
        ele_v = v.get('elevation', 0)
        
        diff = ele_v - ele_u
        if diff > 0: total_climb += diff
        else: total_descent += abs(diff)
    return total_climb, total_descent

def main():
    print("=== NUST Intelligent Navigation System ===")
    
    city = CityGraph()
    city.load_data('data/nodes.json', 'data/edges.json', 'data/pois.json')
    
    if not city.pois:
        print("CRITICAL: No POIs loaded. Run data_pipeline.py first!")
        return

    # 1. Interactive Input
    start_lat, start_lon, start_name = get_user_selection(city.pois, "Select START Point")
    end_lat, end_lon, end_name = get_user_selection(city.pois, "Select DESTINATION")
    
    # 2. Mode Selection
    print("\nSelect Transport Mode:")
    print("  1. Walking (Optimizes for Flat Terrain)")
    print("  2. Driving (Optimizes for Speed)")
    m_choice = input("Choice (1/2): ")
    mode = 'walk' if m_choice == '1' else 'car'
    
    print(f"\n[Process] Snapping '{start_name}' to nearest {mode} road...")
    start_id = city.find_nearest_node(start_lat, start_lon, mode=mode)
    end_id = city.find_nearest_node(end_lat, end_lon, mode=mode)
    
    print(f"[Process] Calculating {mode.upper()} route...")
    path, time_cost = a_star_search(city, start_id, end_id, mode=mode)

    if not path:
        print("Error: No path found.")
        return

    # 3. Analytics
    minutes = time_cost / 60.0
    climb, descent = calculate_stats(city, path)
    
    print(f"\n[Results] Trip to {end_name}:")
    print(f" - Estimated Time: {minutes:.1f} min")
    print(f" - Total Climb: {climb:.1f} meters")
    
    # 4. Nearby POIs
    print("\n[POI] Services along route:")
    found_pois = []
    for i in range(0, len(path), 10): 
        n = city.get_node(path[i])
        found_pois.extend(city.spatial.get_nearby(n['lat'], n['lon']))

    unique_pois = {p['name']: p for p in found_pois if p['name'] not in [start_name, end_name]}.values()
    
    if unique_pois:
        for p in list(unique_pois)[:5]: 
            print(f" - {p['name']}")
    else:
        print(" - None found.")

    # <--- CHANGE 3: Call the Google Maps generator
    generate_map(path, city.nodes)

if __name__ == "__main__":
    main()