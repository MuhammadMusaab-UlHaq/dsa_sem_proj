from .structures import CityGraph
# [Task 3 Fix] Added get_distance_meters to import
from .algorithms import a_star_search, bfs_search, get_distance_meters
from .visualizer import generate_map
import os
import sys

# --- GLOBAL VARIABLES ---
city = None
nav_stack = [] 

# --- NAVIGATION STACK LOGIC ---
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

# --- [TASK 3] CALCULATOR HELPERS ---
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
        if query == '0': return None, None, None
        
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
        except ValueError: pass

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
        if diff > 0: total_climb += diff
        else: total_descent += abs(diff)
    return total_climb, total_descent

# --- MENUS ---

def route_selection_menu():
    print("\n=== FIND A ROUTE ===")
    
    start_lat, start_lon, start_name = get_user_selection(city.pois, "Select START Point")
    if start_name is None: return go_back()

    end_lat, end_lon, end_name = get_user_selection(city.pois, "Select DESTINATION")
    if end_name is None: return go_back()

    print("\nSelect Routing Algorithm:")
    print("  1. Fastest Route (Car - A*)")
    print("  2. Scenic Walk (Flat - A*)")
    print("  3. Simplest Route (Fewest Turns - BFS)")
    print("  0. Back")
    
    choice = input("Enter choice: ")
    if choice == '0': return go_back()
    
    path = None
    time_cost = 0
    mode = 'car'
    
    if choice == '1':
        print("[System] Calculating Fastest Route...")
        start_id = city.find_nearest_node(start_lat, start_lon, mode='car')
        end_id = city.find_nearest_node(end_lat, end_lon, mode='car')
        path, time_cost = a_star_search(city, start_id, end_id, mode='car')
        
    elif choice == '2':
        print("[System] Calculating Walking Route...")
        mode = 'walk'
        start_id = city.find_nearest_node(start_lat, start_lon, mode='walk')
        end_id = city.find_nearest_node(end_lat, end_lon, mode='walk')
        path, time_cost = a_star_search(city, start_id, end_id, mode='walk')
        
    elif choice == '3':
        print("[System] Calculating Simplest Route...")
        start_id = city.find_nearest_node(start_lat, start_lon, mode='car')
        end_id = city.find_nearest_node(end_lat, end_lon, mode='car')
        path, turns = bfs_search(city, start_id, end_id)
        if path: print(f"Info: Path found with {turns} intersections.")

    # [TASK 3] INTEGRATING THE CALCULATOR LOGIC HERE
    if path:
        # 1. Calculate Real Distance
        real_dist = calculate_exact_distance(city, path)
        
        # 2. Display Fuel/Calorie Stats
        display_trip_stats(mode, real_dist, time_cost)
        
        # 3. Display Elevation Stats (Existing)
        climb, descent = calculate_stats(city, path)
        print(f" - Total Climb: {climb:.1f} m")
        print(f" - Total Descent: {descent:.1f} m")
        
        generate_map(path, city.nodes)
    else:
        print("Error: No path found.")
    
    input("Press Enter to return...")
    go_back()

def main_menu():
    print("\n=== NUST Intelligent Navigation System ===")
    print("1. Find Route")
    print("2. Exit")
    
    choice = input("Select Option: ")
    if choice == '1':
        nav_stack.append(main_menu)
        route_selection_menu()
    elif choice == '2': sys.exit()
    else: main_menu()

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
    main_menu()

if __name__ == "__main__":
    main()