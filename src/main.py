from structures import CityGraph
# Import all algorithms from both branches
from algorithms import (
    a_star_search, 
    get_k_shortest_paths, 
    simulate_traffic, 
    reset_traffic,
    bfs_search,
    get_distance_meters
)
from visualizer import generate_map
from history_manager import log_trip, get_history
import os
import sys

# --- GLOBAL VARIABLES ---
city = None
nav_stack = []

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
        print("Exiting application.")
        sys.exit()

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
        # Formula: (Distance_km) * 150 PKR
        cost = (distance_meters / 1000) * 150
        print(f"Est. Fuel Cost : PKR {cost:.2f}")
    elif mode == 'walk':
        # Formula: (Distance_km) * 50 Kcal
        cals = (distance_meters / 1000) * 50
        print(f"Calories Burned: {cals:.1f} kcal")
    print("="*30 + "\n")

# --- OTHER HELPERS ---
def get_user_selection(pois_list, prompt_text):
    while True:
        print(f"\n--- {prompt_text} ---")
        query = input("Search Location (or '0' to Go Back): ").lower().strip()
        if query == '0': 
            return None, None, None
        
        matches = [p for p in pois_list if query in p['name'].lower()]
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
        ele_u = u.get('elevation', 0)
        ele_v = v.get('elevation', 0)
        diff = ele_v - ele_u
        if diff > 0: 
            total_climb += diff
        else: 
            total_descent += abs(diff)
    return total_climb, total_descent

# --- ROUTE SELECTION MENU (Farida's BFS integration) ---
def route_selection_menu():
    print("\n=== FIND A ROUTE ===")
    
    start_lat, start_lon, start_name = get_user_selection(city.pois, "Select START Point")
    if start_name is None: 
        return go_back()

    # Prevent same start/end
    while True:
        end_lat, end_lon, end_name = get_user_selection(city.pois, "Select DESTINATION")
        if end_name is None: 
            return go_back()
        
        if start_name == end_name:
            print(f"\n⚠️  Invalid Selection: You are already at '{start_name}'.")
            print("   Please select a different destination.")
            continue
        break

    print("\nSelect Routing Algorithm:")
    print("  1. Fastest Route (Car - A*)")
    print("  2. Scenic Walk (Flat - A*)")
    print("  3. Simplest Route (Fewest Turns - BFS)")
    print("  4. K-Shortest Paths (3 Alternatives)")
    print("  0. Back")
    
    choice = input("Enter choice: ")
    if choice == '0': 
        return go_back()
    
    path = None
    time_cost = 0
    mode = 'car'
    
    # Get transport mode for all except BFS
    if choice != '3':
        print("\nSelect Transport Mode:")
        print("  1. Walking (Optimizes for Flat Terrain)")
        print("  2. Driving (Optimizes for Speed)")
        m_choice = input("Choice (1/2): ")
        mode = 'walk' if m_choice == '1' else 'car'
    
    print(f"\n[Process] Snapping '{start_name}' to nearest {mode} road...")
    start_id = city.find_nearest_node(start_lat, start_lon, mode=mode)
    end_id = city.find_nearest_node(end_lat, end_lon, mode=mode)
    
    if choice == '1':
        print("[System] Calculating Fastest Route...")
        path, time_cost = a_star_search(city, start_id, end_id, mode='car')
        
    elif choice == '2':
        print("[System] Calculating Walking Route...")
        mode = 'walk'
        path, time_cost = a_star_search(city, start_id, end_id, mode='walk')
        
    elif choice == '3':
        print("[System] Calculating Simplest Route (BFS)...")
        path, turns = bfs_search(city, start_id, end_id)
        if path: 
            print(f"Info: Path found with {turns} intersections.")
            # Calculate time for stats
            time_cost = len(path) * 30  # Rough estimate
    
    elif choice == '4':
        # Ahmed's K-shortest paths
        print(f"[Process] Calculating {mode.upper()} routes...")
        paths_found = get_k_shortest_paths(city, start_id, end_id, k=3, mode=mode)

        if not paths_found:
            print("Error: No path found.")
            return

        print(f"\n--- Recommended Routes to {end_name} ---")
        path = paths_found[0][0]  # Default to best
        time_cost = paths_found[0][1]
        
        for i, (route_path, cost) in enumerate(paths_found):
            minutes = cost / 60.0
            climb, descent = calculate_stats(city, route_path)
            label = "(Best)" if i == 0 else f"(Alt {i})"
            print(f"Route {i+1} {label}: {minutes:.1f} min | Climb: {climb:.0f}m")

    # Display results for all route types
    if path:
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
        
        # POI Logic
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
        
        generate_map(path, city.nodes)
    else:
        print("Error: No path found.")
    
    input("\nPress Enter to return...")
    go_back()

# --- MAIN MENU ---
def main_menu():
    print("\n=== NUST Intelligent Navigation System ===")
    print("1. Find Route")
    print(f"2. Toggle Rush Hour Mode (Currently: {'ON' if rush_hour_active else 'OFF'})")
    print("3. View Search History")
    print("4. Exit")
    
    choice = input("Select Option: ")
    
    if choice == '1':
        navigate_to(route_selection_menu)
    elif choice == '2':
        toggle_traffic()
    elif choice == '3':
        view_history()
    elif choice == '4':
        sys.exit()
    else:
        main_menu()

# --- TRAFFIC SIMULATION (Ahmed's feature) ---
rush_hour_active = False
traffic_mods = []

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