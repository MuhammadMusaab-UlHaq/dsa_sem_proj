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
from history_manager import log_trip, get_history, get_frequent_destinations
import os
import sys
import time

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
def format_poi_name(name):
    """Properly capitalize POI names for display."""
    # Handle special cases
    special = {
        'nust': 'NUST', 'seecs': 'SEECS', 'scee': 'SCEE', 'smme': 'SMME',
        'sada': 'SADA', 'sns': 'SNS', 'nbs': 'NBS', 'nice': 'NICE',
        'cips': 'CIPS', 'rcms': 'RCMS', 'iaec': 'IAEC', 'asab': 'ASAB',
        'hbl': 'HBL', 'atm': 'ATM', 'c1': 'C1', 'c2': 'C2', 'tic': 'TIC'
    }
    
    words = name.split()
    result = []
    for word in words:
        lower = word.lower().strip('()')
        if lower in special:
            # Preserve parentheses
            if word.startswith('('):
                result.append(f"({special[lower]})")
            elif word.endswith(')'):
                result.append(f"{special[lower]})")
            else:
                result.append(special[lower])
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def get_type_icon(poi_type):
    """Return emoji icon for POI type."""
    # Handle None, NaN, or non-string types
    if poi_type is None or not isinstance(poi_type, str):
        return '📌'
    
    icons = {
        'gate': '🚪',
        'academic': '🏛️',
        'hostel': '🏠',
        'cafe': '☕',
        'restaurant': '🍽️',
        'library': '📚',
        'sports': '⚽',
        'mosque': '🕌',
        'medical': '🏥',
        'admin': '🏢',
        'bank': '🏦',
        'atm': '💳',
        'shop': '🛒',
        'parking': '🅿️',
        'landmark': '📍',
        'research': '🔬',
        'service': '🔧',
        'university': '🎓',
        'fuel': '⛽'
    }
    return icons.get(poi_type.lower(), '📌')


def get_user_selection_with_autocomplete(graph, prompt_text):
    """Interactive location input with Trie-based autocomplete."""
    while True:
        print(f"\n{'─' * 45}")
        print(f"  {prompt_text}")
        print('─' * 45)
        query = input("  Search: ").strip()
        
        if query == '0':
            return None, None, None
        
        if not query:
            print("  ⚠️  Please enter a location name")
            continue
        
        # Try Trie autocomplete
        if hasattr(graph, 'autocomplete'):
            suggestions = graph.autocomplete(query)
            if suggestions:
                print(f"\n  Found {len(suggestions)} match(es):\n")
                for i, suggestion in enumerate(suggestions, 1):
                    poi = suggestion['data']
                    name = format_poi_name(poi.get('name', suggestion['name']))
                    icon = get_type_icon(poi.get('type'))
                    poi_type = poi.get('type', 'location')
                    type_label = poi_type.capitalize() if isinstance(poi_type, str) else 'Location'
                    print(f"    {i}. {icon}  {name}")
                    print(f"       └─ {type_label}")
                
                print()
                try:
                    choice_input = input(f"  Select (1-{len(suggestions)}) or 0 to search again: ").strip()
                    
                    if choice_input == '0':
                        continue
                    
                    choice = int(choice_input)
                    if 1 <= choice <= len(suggestions):
                        selected_poi = suggestions[choice - 1]['data']
                        display_name = format_poi_name(selected_poi['name'])
                        print(f"\n  ✅ Selected: {display_name}")
                        return selected_poi['lat'], selected_poi['lon'], display_name
                    else:
                        print("  ⚠️  Invalid selection, try again")
                except ValueError:
                    print("  ⚠️  Please enter a number")
                continue
        
        # Fallback to linear search
        matches = [p for p in graph.pois if query.lower() in p['name'].lower()]
        if not matches:
            print(f"  ❌ No matches for '{query}'. Try different keywords.")
            print("     Examples: gate, seecs, concordia, library")
            continue
            
        print(f"\n  Found {len(matches)} match(es):\n")
        for i, p in enumerate(matches[:8], 1):
            name = format_poi_name(p['name'])
            icon = get_type_icon(p.get('type', 'poi'))
            print(f"    {i}. {icon}  {name}")
            
        print()
        try:
            choice = int(input(f"  Select (1-{min(len(matches), 8)}): "))
            if 1 <= choice <= min(len(matches), 8):
                selected = matches[choice-1]
                display_name = format_poi_name(selected['name'])
                print(f"\n  ✅ Selected: {display_name}")
                return selected['lat'], selected['lon'], display_name
        except ValueError:
            print("  ⚠️  Please enter a number")

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

def collect_route_data(graph, path, mode, time_cost, start_name, end_name, algo_stats=None):
    """Collect all data needed for visualization."""
    
    # Calculate distances and stats
    real_dist = calculate_exact_distance(graph, path)
    climb, descent = calculate_stats(graph, path)
    
    # Energy calculation
    if mode == 'walk':
        calories = (real_dist / 1000) * 50
        fuel_cost = 0
    else:
        calories = 0
        fuel_cost = (real_dist / 1000) * 150
    
    route_stats = {
        'time_sec': time_cost,
        'distance_m': real_dist,
        'climb_m': climb,
        'descent_m': descent,
        'mode': mode,
        'calories': calories,
        'fuel_cost': fuel_cost
    }
    
    # Get POIs along route
    pois_along = []
    start_node = graph.get_node(path[0])
    if start_node:
        found_pois = []
        for i in range(0, len(path), 10):
            n = graph.get_node(path[i])
            if n:
                found_pois.extend(graph.spatial.get_nearby(n['lat'], n['lon']))
        
        unique_pois = {p['name']: p for p in found_pois 
                       if p['name'] not in [start_name, end_name]}.values()
        
        for p in unique_pois:
            distance = get_distance_meters(start_node, {'lat': p['lat'], 'lon': p['lon']})
            pois_along.append({
                'name': p['name'],
                'type': p.get('type', 'Unknown'),
                'distance_m': distance
            })
        
        # Sort using merge_sort
        pois_along = merge_sort(pois_along, key=lambda x: x['distance_m'])
    
    return route_stats, pois_along[:5]

def display_route_results(path, mode, time_cost, start_name, end_name, algo_stats=None, alternatives=None):
    """Display route results and generate enhanced map."""
    if not path:
        print("Error: No path found.")
        return
    
    # Collect route data
    route_stats, pois_along = collect_route_data(city, path, mode, time_cost, start_name, end_name)
    
    # Display in CLI
    real_dist = route_stats['distance_m']
    display_trip_stats(mode, real_dist, time_cost)
    
    climb, descent = route_stats['climb_m'], route_stats['descent_m']
    print(f" - Total Climb: {climb:.1f} m")
    print(f" - Total Descent: {descent:.1f} m")
    
    # Log trip
    log_trip(start_name, end_name, mode, time_cost/60.0)
    print(">> Trip logged to history.")
    
    # Display POIs
    print("\n[POI] Services along route (sorted by distance):")
    if pois_along:
        for p in pois_along:
            print(f" - {p['name']} ({p['distance_m']:.0f}m away)")
    else:
        print(" - None found.")
    
    # Default algorithm stats if not provided
    if algo_stats is None:
        algo_stats = {
            'algorithm_name': 'A*',
            'nodes_explored': 0,
            'heap_operations': 0,
            'time_ms': 0
        }
    
    # Generate the enhanced map
    generate_map(
        path_nodes=path,
        all_nodes=city.nodes,
        route_stats=route_stats,
        algorithm_stats=algo_stats,
        pois_along_route=pois_along,
        alternatives=alternatives,
        start_name=start_name,
        end_name=end_name
    )


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
    
    # Validate that nodes were found
    if start_id is None:
        print(f"\n❌ Error: Could not find a {mode} route from '{start_name}'.")
        print("   This location may be too far from the road network.")
        input("\nPress Enter to return...")
        return go_back()
    
    if end_id is None:
        print(f"\n❌ Error: Could not find a {mode} route to '{end_name}'.")
        print("   This location may be too far from the road network.")
        input("\nPress Enter to return...")
        return go_back()
    
    path = None
    time_cost = 0
    
    # For A* (choice == '1'):
    if choice == '1':
        print(f"[System] Calculating Fastest {mode.upper()} Route...")
        path, time_cost, algo_stats = a_star_search(city, start_id, end_id, mode=mode, return_stats=True)
        display_route_results(path, mode, time_cost, start_name, end_name, algo_stats=algo_stats)

    # For BFS (choice == '2'):
    elif choice == '2':
        print("[System] Calculating Simplest Route (BFS)...")
        path, turns, algo_stats = bfs_search(city, start_id, end_id, return_stats=True)
        if path:
            print(f"Info: Path found with {turns} intersections.")
            time_cost = len(path) * 30
            display_route_results(path, mode, time_cost, start_name, end_name, algo_stats=algo_stats)
        else:
            print("Error: No path found.")

    # For K-shortest (choice == '3'):
    elif choice == '3':
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
            
            # Get stats for primary route
            _, _, algo_stats = a_star_search(city, start_id, end_id, mode=mode, return_stats=True)
            
            display_route_results(path, mode, time_cost, start_name, end_name, 
                                algo_stats=algo_stats, alternatives=paths_found)
    
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
    
    # Reconstruct full path for visualization AND keep segments separate
    full_path = []
    route_segments = []  # List of segment paths for multi-colored display
    segment_labels = [start_name]  # Labels for each waypoint
    route_nodes = [start_id] + best_order
    
    for i in range(len(route_nodes) - 1):
        segment_key = (route_nodes[i], route_nodes[i+1])
        if segment_key in segments:
            segment_path = segments[segment_key]
            route_segments.append(segment_path)  # Store each segment
            
            # Get label for this stop
            if i < len(best_order):
                stop_name = stops_info[stop_ids.index(best_order[i])][2]
                segment_labels.append(stop_name)
            
            if i == 0:
                full_path.extend(segment_path)
            else:
                full_path.extend(segment_path[1:])
    
    if full_path:
        climb, descent = calculate_stats(city, full_path)
        total_dist = calculate_exact_distance(city, full_path)
        print(f"⛰️  Total Climb: {climb:.0f}m | Descent: {descent:.0f}m")
        
        # Log to history (use ASCII-safe arrow)
        stops_str = " -> ".join([start_name] + [stops_info[stop_ids.index(sid)][2] for sid in best_order])
        log_trip(stops_str[:50], "Multi-Stop", mode, total_cost/60)
        print(">> Route logged to history.")
        
        # Prepare stats for visualizer
        route_stats = {
            'time_sec': total_cost,
            'distance_m': total_dist,
            'climb_m': climb,
            'descent_m': descent,
            'mode': mode,
            'calories': (total_dist / 1000) * 50 if mode == 'walk' else 0,
            'fuel_cost': (total_dist / 1000) * 150 if mode == 'car' else 0
        }
        
        algo_stats = {
            'algorithm_name': 'TSP (Nearest Neighbor)' if len(stop_ids) > 4 else 'TSP (Brute Force)',
            'nodes_explored': len(full_path),
            'heap_operations': len(route_segments),  # Number of segments computed
            'time_ms': 0
        }
        
        generate_map(
            path_nodes=full_path, 
            all_nodes=city.nodes,
            route_stats=route_stats,
            algorithm_stats=algo_stats,
            start_name=start_name,
            end_name=stops_info[stop_ids.index(best_order[-1])][2],
            multi_stop_segments=route_segments,  # Pass segments for multi-colored display
            waypoint_labels=segment_labels  # Pass labels for markers
        )
    
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
    print("\n" + "="*50)
    print("   📜 TRIP HISTORY")
    print("="*50)
    
    # Show frequent destinations
    frequent = get_frequent_destinations(3)
    if frequent:
        print("\n⭐ Most Visited:")
        for dest, count in frequent:
            print(f"   • {dest} ({count} trips)")
    
    # Show recent trips
    print("\n📋 Recent Trips:")
    print("-"*50)
    history = get_history(10)
    for line in history:
        # Format nicely
        line = line.strip()
        if line and not line.startswith("No") and not line.startswith("History"):
            # Parse timestamp
            try:
                parts = line.split("] ")
                timestamp = parts[0].replace("[", "")
                route_info = parts[1] if len(parts) > 1 else line
                print(f"  {timestamp}")
                print(f"    → {route_info}")
                print()
            except:
                print(f"  {line}")
        else:
            print(f"  {line}")
    
    print("-"*50)
    input("\nPress Enter to return...")
    main_menu()

# --- MAIN MENU ---
def main_menu():
    global rush_hour_active
    print("\n")
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║     🌸 NUST Intelligent Navigation System     ║")
    print("  ╠═══════════════════════════════════════════════╣")
    print("  ║                                               ║")
    print("  ║   1. 🗺️  Find Route (A* / BFS)                ║")
    print("  ║   2. 📍 Multi-Stop Route (TSP)                ║")
    traffic_status = "🔴 ON" if rush_hour_active else "⚪ OFF"
    print(f"  ║   3. 🚦 Rush Hour Mode [{traffic_status}]              ║")
    print("  ║   4. 📜 View Trip History                     ║")
    print("  ║   5. 🚪 Exit                                  ║")
    print("  ║                                               ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()
    
    choice = input("  Select option: ").strip()
    
    if choice == '1':
        navigate_to(route_selection_menu)
    elif choice == '2':
        navigate_to(multi_stop_route_menu)
    elif choice == '3':
        toggle_traffic()
    elif choice == '4':
        view_history()
    elif choice == '5':
        print("\n  👋 Goodbye! Safe travels.\n")
        sys.exit()
    else:
        print("  ⚠️  Invalid option")
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