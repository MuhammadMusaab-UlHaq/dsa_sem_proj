from structures import CityGraph, merge_sort
from algorithms import (
    a_star_search, 
    get_k_shortest_paths, 
    simulate_traffic, 
    reset_traffic,
    bfs_search,
    get_distance_meters,
    optimize_route_order
)
from visualizer import generate_map
from history_manager import log_trip, get_history
import os
import sys

# --- GLOBAL VARIABLES ---
city = None
nav_stack = []
rush_hour_active = False
traffic_mods = []

# --- NAVIGATION STACK LOGIC (Task 2 - Farida) ---
def navigate_to(next_func):
    """Pushes current menu to stack and executes next."""
    nav_stack.append(main_menu)
    next_func()

def go_back():
    """Returns to previous menu."""
    if nav_stack:
        previous_func = nav_stack.pop()
        previous_func()
    else:
        main_menu()

# --- [TASK 3] CALCULATOR HELPERS (Farida) ---
def calculate_exact_distance(graph, path):
    """Sum the precise distance in meters between path nodes."""
    total_dist = 0.0
    for i in range(len(path) - 1):
        u = graph.nodes[path[i]]
        v = graph.nodes[path[i+1]]
        total_dist += get_distance_meters(u, v)
    return total_dist

def display_trip_stats(mode, distance_meters, time_seconds):
    """Calculates and prints Fuel Cost or Calories."""
    print("\n" + "="*30)
    print(f"   TRIP STATISTICS ({mode.upper()})")
    print("="*30)
    print(f"Est. Time      : {time_seconds/60:.1f} min")
    print(f"Total Distance : {distance_meters:.0f} meters")
    
    if mode == 'car':
        cost = (distance_meters / 1000) * 150
        print(f"Est. Fuel Cost : PKR {cost:.2f}")
    elif mode == 'walk':
        cals = (distance_meters / 1000) * 50
        print(f"Calories Burned: {cals:.1f} kcal")
    print("="*30 + "\n")

# --- USER SELECTION WITH TRIE AUTOCOMPLETE (Usman) ---
def get_user_selection_with_autocomplete(graph, prompt_text):
    """Interactive location input with Trie-based autocomplete"""
    while True:
        print(f"\n--- {prompt_text} ---")
        query = input("Type location name (or '0' to Go Back): ").strip()
        
        if query == '0':
            return None, None, None
        
        if not query:
            print("❌ Empty input! Please try again.")
            continue
        
        # Try Trie autocomplete first
        if hasattr(graph, 'autocomplete'):
            suggestions = graph.autocomplete(query)
            if suggestions:
                print(f"\n📍 Found {len(suggestions)} match(es):")
                for i, suggestion in enumerate(suggestions, 1):
                    poi = suggestion['data']
                    print(f"  {i}. {suggestion['name']} ({poi.get('type', 'Unknown')})")
                
                try:
                    choice = int(input(f"\nSelect location (1-{len(suggestions)}, 0 to search again): "))
                    if choice == 0:
                        continue
                    if 1 <= choice <= len(suggestions):
                        selected_poi = suggestions[choice - 1]['data']
                        return selected_poi['lat'], selected_poi['lon'], selected_poi['name']
                    else:
                        print("❌ Invalid selection!")
                except ValueError:
                    print("❌ Please enter a number!")
                continue
        
        # Fallback to linear search
        matches = [p for p in graph.pois if query.lower() in p['name'].lower()]
        if not matches:
            print("No matches found. Try again.")
            continue
            
        print(f"Found {len(matches)} matches:")
        for i, p in enumerate(matches[:5]):
            print(f"  {i+1}. {p['name']} ({p['type']})")
            
        try:
            choice = int(input("Select number: "))
            if 1 <= choice <= len(matches):
                selected = matches[choice-1]
                return selected['lat'], selected['lon'], selected['name']
        except ValueError:
            pass

def calculate_stats(graph, path):
    """Calculates elevation gain/loss."""
    total_climb = 0
    total_descent = 0
    for i in range(len(path) - 1):
        u = graph.nodes[path[i]]
        v = graph.nodes[path[i+1]]
        ele_u = u.get('ele', u.get('elevation', 0))
        ele_v = v.get('ele', v.get('elevation', 0))
        diff = ele_v - ele_u
        if diff > 0: 
            total_climb += diff
        else: 
            total_descent += abs(diff)
    return total_climb, total_descent

def display_route_results(path, mode, time_cost, start_name, end_name):
    """Common function to display route results and generate map."""
    if not path:
        print("Error: No path found.")
        return
    
    # Calculate real distance (Farida's feature)
    real_dist = calculate_exact_distance(city, path)
    
    # Display Fuel/Calorie Stats (Farida's feature)
    display_trip_stats(mode, real_dist, time_cost)
    
    # Display Elevation Stats
    climb, descent = calculate_stats(city, path)
    print(f" - Total Climb: {climb:.1f} m")
    print(f" - Total Descent: {descent:.1f} m")
    
    # Log trip (Ahmed's feature)
    log_trip(start_name, end_name, mode, time_cost/60.0)
    print(">> Trip logged to history.")
    
    # POI Logic with Merge Sort (Usman's feature)
    print("\n[POI] Services along route (sorted by distance):")
    found_pois = []
    for i in range(0, len(path), 10): 
        n = city.get_node(path[i])
        if n:
            found_pois.extend(city.spatial.get_nearby(n['lat'], n['lon']))

    unique_pois = {p['name']: p for p in found_pois if p['name'] not in [start_name, end_name]}.values()
    
    if unique_pois:
        # Calculate distance and sort using merge_sort (Usman's feature)
        start_node = city.get_node(path[0])
        poi_list = []
        for p in unique_pois:
            distance = get_distance_meters(start_node, {'lat': p['lat'], 'lon': p['lon']})
            poi_list.append({'poi': p, 'distance': distance})
        
        sorted_pois = merge_sort(poi_list, key=lambda x: x['distance'])
        
        for item in sorted_pois[:5]:
            p = item['poi']
            dist_m = item['distance']
            print(f" - {p['name']} ({dist_m:.0f}m away)")
    else:
        print(" - None found.")
    
    generate_map(path, city.nodes)

# --- ROUTE SELECTION MENU ---
def route_selection_menu():
    print("\n=== FIND A ROUTE ===")
    
    start_lat, start_lon, start_name = get_user_selection_with_autocomplete(city, "Select START Point")
    if start_name is None: 
        return go_back()

    # Prevent same start/end
    while True:
        end_lat, end_lon, end_name = get_user_selection_with_autocomplete(city, "Select DESTINATION")
        if end_name is None: 
            return go_back()
        
        if start_name == end_name:
            print(f"\n⚠️  Invalid Selection: You are already at '{start_name}'.")
            print("   Please select a different destination.")
            continue
        break

    print("\nSelect Routing Algorithm:")
    print("  1. Fastest Route (A*)")
    print("  2. Simplest Route (Fewest Turns - BFS)")
    print("  3. K-Shortest Paths (3 Alternatives)")
    print("  0. Back")
    
    choice = input("Enter choice: ")
    if choice == '0': 
        return go_back()
    
    # Get transport mode
    print("\nSelect Transport Mode:")
    print("  1. Walking (Optimizes for Flat Terrain)")
    print("  2. Driving (Optimizes for Speed)")
    m_choice = input("Choice (1/2): ")
    mode = 'walk' if m_choice == '1' else 'car'
    
    print(f"\n[Process] Snapping '{start_name}' to nearest {mode} road...")
    start_id = city.find_nearest_node(start_lat, start_lon, mode=mode)
    end_id = city.find_nearest_node(end_lat, end_lon, mode=mode)
    
    path = None
    time_cost = 0
    
    if choice == '1':
        print(f"[System] Calculating Fastest {mode.upper()} Route...")
        path, time_cost = a_star_search(city, start_id, end_id, mode=mode)
        display_route_results(path, mode, time_cost, start_name, end_name)
        
    elif choice == '2':
        print("[System] Calculating Simplest Route (BFS)...")
        path, turns = bfs_search(city, start_id, end_id)
        if path: 
            print(f"Info: Path found with {turns} intersections.")
            time_cost = len(path) * 30  # Rough estimate
            display_route_results(path, mode, time_cost, start_name, end_name)
        else:
            print("Error: No path found.")
    
    elif choice == '3':
        # Ahmed's K-shortest paths
        print(f"[Process] Calculating {mode.upper()} routes...")
        paths_found = get_k_shortest_paths(city, start_id, end_id, k=3, mode=mode)

        if not paths_found:
            print("Error: No path found.")
        else:
            print(f"\n--- Recommended Routes to {end_name} ---")
            
            for i, (route_path, cost) in enumerate(paths_found):
                minutes = cost / 60.0
                climb, descent = calculate_stats(city, route_path)
                label = "(Best)" if i == 0 else f"(Alt {i})"
                print(f"Route {i+1} {label}: {minutes:.1f} min | Climb: {climb:.0f}m")
            
            path = paths_found[0][0]
            time_cost = paths_found[0][1]
            display_route_results(path, mode, time_cost, start_name, end_name)
    
    input("\nPress Enter to return...")
    go_back()

# --- TSP MULTI-STOP ROUTE (Usman's feature) ---
def multi_stop_route_menu():
    print("\n=== OPTIMIZE MULTI-STOP ROUTE (Errand Runner) ===")
    print("Plan an efficient route visiting multiple locations")
    
    # Get starting point
    start_lat, start_lon, start_name = get_user_selection_with_autocomplete(city, "Select STARTING Point")
    if start_name is None:
        return go_back()
    
    # Select transport mode
    print("\nSelect Transport Mode:")
    print("  1. Walking")
    print("  2. Driving")
    m_choice = input("Choice (1/2): ")
    mode = 'walk' if m_choice == '1' else 'car'
    
    # Get number of stops
    print("\nHow many stops do you want to visit? (Recommended: 2-5)")
    try:
        num_stops = int(input("Number of stops: "))
        if num_stops < 2 or num_stops > 6:
            print("⚠️  Please choose between 2-6 stops for optimal performance")
            input("Press Enter to return...")
            return go_back()
    except ValueError:
        print("❌ Invalid number")
        input("Press Enter to return...")
        return go_back()
    
    # Collect all stops
    stops_info = []
    stop_names = [start_name]
    
    for i in range(num_stops):
        while True:
            stop_lat, stop_lon, stop_name = get_user_selection_with_autocomplete(
                city, f"Select STOP #{i+1}"
            )
            if stop_name is None:
                return go_back()
            
            if stop_name in stop_names:
                print(f"⚠️  You've already selected '{stop_name}'. Choose a different location.")
                continue
            
            stop_names.append(stop_name)
            stops_info.append((stop_lat, stop_lon, stop_name))
            break
    
    # Snap all locations to graph nodes
    print(f"\n[Process] Snapping locations to {mode} roads...")
    start_id = city.find_nearest_node(start_lat, start_lon, mode=mode)
    stop_ids = []
    
    for stop_lat, stop_lon, stop_name in stops_info:
        stop_id = city.find_nearest_node(stop_lat, stop_lon, mode=mode)
        stop_ids.append(stop_id)
    
    # Run TSP optimization
    print(f"[Process] Optimizing route order for {num_stops} stops...")
    best_order, total_cost, segments = optimize_route_order(city, start_id, stop_ids, mode)
    
    if not best_order:
        print("❌ Could not find valid route")
        input("Press Enter to return...")
        return go_back()
    
    # Display results
    print(f"\n{'='*60}")
    print("📍 OPTIMIZED ROUTE ORDER")
    print(f"{'='*60}")
    print(f"🏁 Start: {start_name}")
    
    for idx, stop_id in enumerate(best_order, 1):
        stop_name = stops_info[stop_ids.index(stop_id)][2]
        print(f"   ↓")
        print(f"{idx}. {stop_name}")
    
    print(f"\n⏱️  Total Estimated Time: {total_cost/60:.1f} minutes")
    print(f"🚗 Transport Mode: {mode.upper()}")
    print(f"{'='*60}")
    
    # Reconstruct full path for visualization
    full_path = []
    route_nodes = [start_id] + best_order
    
    for i in range(len(route_nodes) - 1):
        segment_key = (route_nodes[i], route_nodes[i+1])
        if segment_key in segments:
            segment_path = segments[segment_key]
            if i == 0:
                full_path.extend(segment_path)
            else:
                full_path.extend(segment_path[1:])
    
    if full_path:
        climb, descent = calculate_stats(city, full_path)
        print(f"⛰️  Total Climb: {climb:.0f}m | Descent: {descent:.0f}m")
        
        # Log to history
        stops_str = " → ".join([start_name] + [stops_info[stop_ids.index(sid)][2] for sid in best_order])
        log_trip(stops_str[:50], "Multi-Stop", mode, total_cost/60)
        print(">> Route logged to history.")
        
        generate_map(full_path, city.nodes)
    
    input("\nPress Enter to return to main menu...")
    go_back()

# --- TRAFFIC SIMULATION (Ahmed's feature) ---
def toggle_traffic():
    global rush_hour_active, traffic_mods
    if not rush_hour_active:
        traffic_mods = simulate_traffic(city)
        rush_hour_active = True
        print(">> Rush Hour Mode ACTIVATED. Highways are slower.")
    else:
        reset_traffic(city, traffic_mods)
        rush_hour_active = False
        traffic_mods = []
        print(">> Rush Hour Mode DEACTIVATED.")
    input("\nPress Enter to return...")
    main_menu()

# --- VIEW HISTORY (Ahmed's feature) ---
def view_history():
    print("\n--- Search History ---")
    history = get_history()
    for line in history:
        print(line.strip())
    input("\nPress Enter to return...")
    main_menu()

# --- MAIN MENU ---
def main_menu():
    global rush_hour_active
    print("\n" + "="*50)
    print("   NUST Intelligent Navigation System")
    print("="*50)
    print("1. Find Route (A*/BFS)")
    print("2. Optimize Multi-Stop Route (TSP)")
    print(f"3. Toggle Rush Hour Mode ({'ON 🚦' if rush_hour_active else 'OFF'})")
    print("4. View Search History")
    print("5. Exit")
    print("="*50)
    
    choice = input("Select Option: ")
    
    if choice == '1':
        navigate_to(route_selection_menu)
    elif choice == '2':
        navigate_to(multi_stop_route_menu)
    elif choice == '3':
        toggle_traffic()
    elif choice == '4':
        view_history()
    elif choice == '5':
        print("Goodbye!")
        sys.exit()
    else:
        main_menu()

# --- MAIN FUNCTION ---
def main():
    global city
    city = CityGraph()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    print("[System] Loading Map Data...")
    try:
        city.load_data(
            os.path.join(data_dir, 'nodes.json'), 
            os.path.join(data_dir, 'edges.json'), 
            os.path.join(data_dir, 'pois.json')
        )
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    if not city.pois:
        print("CRITICAL: No POIs loaded. Run data_pipeline.py first!")
        return
    
    main_menu()

if __name__ == "__main__":
    main()