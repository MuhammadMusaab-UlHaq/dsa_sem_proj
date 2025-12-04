from structures import CityGraph
from algorithms import a_star_search, get_k_shortest_paths, simulate_traffic, reset_traffic
from visualizer import generate_map 
from history_manager import log_trip, get_history
import os

def get_user_selection_with_autocomplete(graph, prompt_text):
    """Interactive location input with Trie-based autocomplete (Task 1)"""
    while True:
        print(f"\n--- {prompt_text} ---")
        query = input("Type location name: ").strip()
        
        if not query:
            print("❌ Empty input! Please try again.")
            continue
        
        # Get autocomplete suggestions using Trie
        suggestions = graph.autocomplete(query)
        
        if not suggestions:
            print(f"❌ No locations found matching '{query}'. Try different keywords.")
            continue
        
        # Display suggestions
        print(f"\n📍 Found {len(suggestions)} match(es):")
        for i, suggestion in enumerate(suggestions, 1):
            poi = suggestion['data']
            print(f"  {i}. {suggestion['name']} ({poi.get('type', 'Unknown')})")
        
        # User selection
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

def calculate_stats(graph, path):
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

def main():
    print("=== NUST Intelligent Navigation System ===")
    
    city = CityGraph()
    
    # Locate data relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    city.load_data(
        os.path.join(data_dir, 'nodes.json'), 
        os.path.join(data_dir, 'edges.json'), 
        os.path.join(data_dir, 'pois.json')
    )
    
    if not city.pois:
        print("CRITICAL: No POIs loaded. Run data_pipeline.py first!")
        return

    # --- MAIN MENU LOOP ---
    rush_hour_active = False
    traffic_mods = []

    while True:
        print("\n=== MAIN MENU ===")
        print("1. Plan a Trip")
        print(f"2. Toggle Rush Hour Mode (Currently: {'ON' if rush_hour_active else 'OFF'})")
        print("3. View Search History")
        print("4. Exit")
        
        menu_choice = input("Select option: ")
        
        if menu_choice == '2':
            # Task 2: Traffic Simulation Integration
            if not rush_hour_active:
                traffic_mods = simulate_traffic(city)
                rush_hour_active = True
                print(">> Rush Hour Mode ACTIVATED. Highways are slower.")
            else:
                reset_traffic(city, traffic_mods)
                rush_hour_active = False
                traffic_mods = []
                print(">> Rush Hour Mode DEACTIVATED.")
            continue
            
        elif menu_choice == '3':
            # Task 3: History Integration
            print("\n--- Search History ---")
            history = get_history()
            for line in history:
                print(line.strip())
            input("\nPress Enter to return...")
            continue
            
        elif menu_choice == '4':
            print("Goodbye!")
            break
            
        elif menu_choice == '1':
            pass # Continue to Trip Logic
        else:
            print("Invalid option.")
            continue

        # --- TRIP PLANNING (Using Trie Autocomplete - Task 1) ---
        start_lat, start_lon, start_name = get_user_selection_with_autocomplete(city, "Select START Point")
        
        # --- NEW VALIDATION: Prevent Same Start/End Node ---
        while True:
            end_lat, end_lon, end_name = get_user_selection_with_autocomplete(city, "Select DESTINATION")
            
            if start_name == end_name:
                print(f"\n⚠️  Invalid Selection: You are already at '{start_name}'.")
                print("   Please select a different destination.")
                continue # Loop back
            break # Validation passed
        # ---------------------------------------------------
        
        print("\nSelect Transport Mode:")
        print("  1. Walking (Optimizes for Flat Terrain)")
        print("  2. Driving (Optimizes for Speed)")
        m_choice = input("Choice (1/2): ")
        mode = 'walk' if m_choice == '1' else 'car'
        
        print(f"\n[Process] Snapping '{start_name}' to nearest {mode} road...")
        start_id = city.find_nearest_node(start_lat, start_lon, mode=mode)
        end_id = city.find_nearest_node(end_lat, end_lon, mode=mode)
        
        print(f"[Process] Calculating {mode.upper()} routes...")
        
        # Task 1: K-Shortest Paths Integration
        paths_found = get_k_shortest_paths(city, start_id, end_id, k=3, mode=mode)

        if not paths_found:
            print("Error: No path found.")
            continue

        print(f"\n--- Recommended Routes to {end_name} ---")
        best_path = paths_found[0][0] # Default to best
        
        for i, (path, cost) in enumerate(paths_found):
            minutes = cost / 60.0
            climb, descent = calculate_stats(city, path)
            label = "(Best)" if i == 0 else f"(Alt {i})"
            print(f"Route {i+1} {label}: {minutes:.1f} min | Climb: {climb:.0f}m")
        
        # Log the BEST trip to history (Task 3 Integration)
        best_time = paths_found[0][1] / 60.0
        log_trip(start_name, end_name, mode, best_time)
        print(">> Trip logged to history.")

        # POI Logic (Using Best Path)
        print("\n[POI] Services along best route:")
        found_pois = []
        for i in range(0, len(best_path), 10): 
            n = city.get_node(best_path[i])
            found_pois.extend(city.spatial.get_nearby(n['lat'], n['lon']))

        unique_pois = {p['name']: p for p in found_pois if p['name'] not in [start_name, end_name]}.values()
        
        if unique_pois:
            for p in list(unique_pois)[:5]: 
                print(f" - {p['name']}")
        else:
            print(" - None found.")

        generate_map(best_path, city.nodes)

if __name__ == "__main__":
    main()