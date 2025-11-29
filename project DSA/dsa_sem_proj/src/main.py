from .structures import CityGraph
from .algorithms import a_star_search, bfs_search
from .visualizer import generate_map
import os
import sys

# --- GLOBAL VARIABLES ---
city = None
nav_stack = []  # Task 2: Navigation Stack

# --- NAVIGATION STACK LOGIC ---
def navigate_to(next_func):
    """Pushes the current menu to stack and executes the next."""
    # We push the main_menu as the return point
    nav_stack.append(main_menu) 
    next_func()

def go_back():
    """Returns to the previous menu."""
    if nav_stack:
        previous_func = nav_stack.pop()
        previous_func()
    else:
        print("Exiting application.")
        sys.exit()

# --- HELPER FUNCTIONS ---

def get_user_selection(pois_list, prompt_text):
    while True:
        print(f"\n--- {prompt_text} ---")
        query = input("Search Location (or '0' to Go Back): ").lower().strip()
        
        # [Task 2] Handle Back Button
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
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter a number.")

def calculate_stats(graph, path):
    """Existing logic: Calculates elevation gain/loss."""
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
    
    # 1. Select Start
    start_lat, start_lon, start_name = get_user_selection(city.pois, "Select START Point")
    if start_name is None: return go_back()

    # 2. Select End
    end_lat, end_lon, end_name = get_user_selection(city.pois, "Select DESTINATION")
    if end_name is None: return go_back()

    # 3. Mode Selection (Task 2: Back Button added)
    print("\nSelect Routing Algorithm:")
    print("  1. Fastest Route (Car - A*)")
    print("  2. Scenic Walk (Flat - A* + Tobler)")
    print("  3. Simplest Route (Fewest Turns - BFS)")
    print("  0. Back")
    
    choice = input("Enter choice: ")
    
    if choice == '0': return go_back()
    
    path = None
    time_cost = 0
    mode = 'car'
    
    # Logic integrating BFS from Task 1
    if choice == '1':
        print("[Process] Calculating Fastest Car Route...")
        start_id = city.find_nearest_node(start_lat, start_lon, mode='car')
        end_id = city.find_nearest_node(end_lat, end_lon, mode='car')
        path, time_cost = a_star_search(city, start_id, end_id, mode='car')
        
    elif choice == '2':
        print("[Process] Calculating Flat Walking Route...")
        mode = 'walk'
        start_id = city.find_nearest_node(start_lat, start_lon, mode='walk')
        end_id = city.find_nearest_node(end_lat, end_lon, mode='walk')
        path, time_cost = a_star_search(city, start_id, end_id, mode='walk')
        
    elif choice == '3':
        print("[Process] Calculating Simplest Route (BFS)...")
        start_id = city.find_nearest_node(start_lat, start_lon, mode='car')
        end_id = city.find_nearest_node(end_lat, end_lon, mode='car')
        # BFS logic integration
        path, turns = bfs_search(city, start_id, end_id)
        if path: print(f"Info: Path found with {turns} intersections.")

    # 4. Results
    if path:
        # We use existing calculate_stats (elevation) here. 
        # Fuel Calc (Task 3) will be added in the NEXT commit.
        climb, descent = calculate_stats(city, path)
        minutes = time_cost / 60.0
        
        print(f"\n[Results] Trip to {end_name}:")
        if choice != '3': # BFS doesn't return time
            print(f" - Est. Time: {minutes:.1f} min")
        print(f" - Total Climb: {climb:.1f} m")
        print(f" - Total Descent: {descent:.1f} m")
        
        generate_map(path, city.nodes)
    else:
        print("Error: No path found.")
    
    # Pausing before returning
    input("\nPress Enter to return to menu...")
    go_back()

def main_menu():
    print("\n=== NUST Intelligent Navigation System ===")
    print("1. Find Route")
    print("2. Exit")
    
    choice = input("Select Option: ")
    
    if choice == '1':
        # [Task 2] Push current state and navigate
        nav_stack.append(main_menu)
        route_selection_menu()
    elif choice == '2':
        print("Exiting...")
        sys.exit()
    else:
        print("Invalid selection.")
        main_menu()

def main():
    global city
    city = CityGraph()
    
    # === DATA LOADING ===
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

    # Start the application
    main_menu()

if __name__ == "__main__":
    main()