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
from datetime import datetime, timedelta

# --- GLOBAL VARIABLES ---
city = None
nav_stack = []
rush_hour_active = False
traffic_mods = []

# --- TIME-BASED RUSH HOUR DETECTION ---
def is_rush_hour(check_time=None):
    """
    Check if given time falls within rush hour periods.
    Morning: 7:00 AM - 9:30 AM
    Evening: 4:30 PM - 8:00 PM
    """
    if check_time is None:
        check_time = datetime.now()
    
    hour = check_time.hour
    minute = check_time.minute
    time_decimal = hour + minute / 60.0
    
    # Morning rush: 7:00 - 9:30
    if 7.0 <= time_decimal <= 9.5:
        return True, "Morning Rush"
    # Evening rush: 16:30 - 20:00
    if 16.5 <= time_decimal <= 20.0:
        return True, "Evening Rush"
    return False, None

def get_rush_hour_status():
    """Get human-readable rush hour status."""
    is_rush, period = is_rush_hour()
    now = datetime.now()
    
    if is_rush:
        return f"🔴 {period} Active ({now.strftime('%I:%M %p')})"
    
    # Calculate time until next rush hour
    hour = now.hour
    if hour < 7:
        next_rush = now.replace(hour=7, minute=0, second=0)
        mins = int((next_rush - now).total_seconds() / 60)
        return f"⚪ Clear - Rush starts in {mins} min"
    elif hour < 16:
        next_rush = now.replace(hour=16, minute=30, second=0)
        mins = int((next_rush - now).total_seconds() / 60)
        hrs = mins // 60
        mins = mins % 60
        return f"⚪ Clear - Rush in {hrs}h {mins}m"
    else:
        return f"⚪ Clear - Next rush tomorrow 7 AM"

def estimate_travel_delay(graph, start_id, end_id, mode='car'):
    """
    Calculate the estimated delay due to rush hour traffic.
    Returns (normal_time, rush_time, delay_seconds).
    """
    # Calculate normal time
    normal_path, normal_cost = a_star_search(graph, start_id, end_id, mode)
    if not normal_path:
        return None, None, None
    
    # Temporarily apply traffic and calculate rush time
    mods = simulate_traffic_silent(graph)
    rush_path, rush_cost = a_star_search(graph, start_id, end_id, mode)
    reset_traffic_silent(graph, mods)
    
    if not rush_path:
        return normal_cost, normal_cost, 0
    
    delay = rush_cost - normal_cost
    return normal_cost, rush_cost, max(0, delay)

def simulate_traffic_silent(graph):
    """Apply traffic without printing messages."""
    graph.rush_hour_active = True
    return []

def reset_traffic_silent(graph, modifications=None):
    """Reset traffic without printing messages."""
    graph.rush_hour_active = False

def format_time_seconds(seconds):
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{int(seconds)} sec"
    elif seconds < 3600:
        mins = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{mins} min {secs} sec" if secs > 0 else f"{mins} min"
    else:
        hrs = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hrs}h {mins}m"

def calculate_departure_time(arrival_time_str, travel_seconds, with_traffic=False):
    """
    Calculate when to leave to arrive by target time.
    arrival_time_str: format "HH:MM" (24-hour)
    Returns departure datetime.
    """
    now = datetime.now()
    try:
        target_hour, target_min = map(int, arrival_time_str.split(':'))
        arrival = now.replace(hour=target_hour, minute=target_min, second=0)
        if arrival < now:
            arrival += timedelta(days=1)  # Next day
        
        # Add buffer for traffic uncertainty
        buffer = travel_seconds * 0.15 if with_traffic else travel_seconds * 0.05
        departure = arrival - timedelta(seconds=travel_seconds + buffer)
        return departure
    except:
        return None

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
                'distance_m': distance,
                'lat': p['lat'],
                'lon': p['lon']
            })
        
        # Sort using merge_sort
        pois_along = merge_sort(pois_along, key=lambda x: x['distance_m'])
    
    return route_stats, pois_along[:10]  # Show top 10 POIs along route

def display_route_results(path, mode, time_cost, start_name, end_name, algo_stats=None, alternatives=None):
    """Display route results and generate enhanced map."""
    if not path:
        print("Error: No path found.")
        return
    
    # Display algorithm stats if available
    if algo_stats and algo_stats.get('nodes_explored', 0) > 0:
        print("\n" + "-"*40)
        print(f"  📊 Algorithm: {algo_stats.get('algorithm_name', 'Unknown')}")
        print(f"  🔍 Nodes Explored: {algo_stats.get('nodes_explored', 0):,}")
        if algo_stats.get('heap_operations', 0) > 0:
            print(f"  📦 Heap Operations: {algo_stats.get('heap_operations', 0):,}")
        print(f"  ⏱️  Compute Time: {algo_stats.get('time_ms', 0):.1f} ms")
        print("-"*40)
    
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
            # Calculate actual travel time based on distance and mode
            dist_m = calculate_exact_distance(city, path)
            if mode == 'walk':
                time_cost = dist_m / 1.35  # 1.35 m/s = ~5 km/h walking
            else:
                time_cost = dist_m / 11.11  # 11.11 m/s = ~40 km/h average driving
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
    
    # Run TSP optimization (now returns algo_stats)
    print(f"[Process] Optimizing route order for {num_stops} stops...")
    best_order, total_cost, segments, algo_stats = optimize_route_order(city, start_id, stop_ids, mode)
    
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
        
        # algo_stats is now returned from optimize_route_order with real values
        # No need to override - just use the stats from TSP optimization
        
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

# --- TRAFFIC SIMULATION (Ahmed's feature) - ENHANCED ---
def toggle_traffic():
    global rush_hour_active, traffic_mods
    
    # Show current time and rush hour status
    now = datetime.now()
    is_rush, period = is_rush_hour()
    
    print("\n" + "="*55)
    print("   🚦 RUSH HOUR TRAFFIC MODE")
    print("="*55)
    print(f"\n   Current Time: {now.strftime('%I:%M %p')}")
    
    if is_rush:
        print(f"   Status: 🔴 {period} - Heavy traffic expected!")
    else:
        print("   Status: ⚪ Normal traffic conditions")
        # Show when next rush hour starts
        hour = now.hour
        if hour < 7:
            print("   Next Rush: Morning rush begins at 7:00 AM")
        elif hour < 16:
            print("   Next Rush: Evening rush begins at 4:30 PM")
        else:
            print("   Next Rush: Tomorrow morning at 7:00 AM")
    
    print("\n" + "-"*55)
    
    if not rush_hour_active:
        print("\n   🟢 Enable rush hour mode to simulate:")
        print("      - 3x slower travel on major roads")
        print("      - Primary roads & highways affected")
        print("      - More realistic route planning")
        if is_rush:
            print("\n   💡 TIP: Rush hour is active now!")
            print("      Enabling mode recommended for accurate timing.")
    else:
        print("\n   🔴 Rush hour mode is currently ACTIVE")
        print("      - Major roads are 3x slower")
        print("      - Routes account for traffic delays")
    
    print("\n" + "-"*55)
    print("   Options:")
    print("   1. Toggle Rush Hour Mode " + ("OFF" if rush_hour_active else "ON"))
    print("   2. View Traffic Impact Analysis")
    print("   3. Trip Time Planner")
    print("   4. Back to Main Menu")
    print()
    
    choice = input("   Select option: ").strip()
    
    if choice == '1':
        if not rush_hour_active:
            traffic_mods = simulate_traffic(city)
            rush_hour_active = True
            print("\n   ✅ Rush Hour Mode ACTIVATED")
            print("      Highways and primary roads are now slower.")
        else:
            reset_traffic(city, traffic_mods)
            rush_hour_active = False
            traffic_mods = []
            print("\n   ✅ Rush Hour Mode DEACTIVATED")
            print("      Traffic cleared - normal speeds restored.")
        input("\n   Press Enter to continue...")
        toggle_traffic()
    elif choice == '2':
        traffic_impact_analysis()
    elif choice == '3':
        trip_time_planner()
    elif choice == '4':
        main_menu()
    else:
        print("   ⚠️  Invalid option")
        toggle_traffic()

def traffic_impact_analysis():
    """Show how rush hour affects common routes."""
    print("\n" + "="*55)
    print("   📊 TRAFFIC IMPACT ANALYSIS")
    print("="*55)
    print("\n   Calculating impact on routes using major roads...\n")
    
    # Define routes that use major roads (NUST to city locations)
    # These are more likely to show traffic impact
    test_routes = [
        ("nust gate 1", "centaurus"),
        ("nust gate 1", "faisal mosque"),
        ("nust main gate", "blue area"),
        ("seecs", "f-6 markaz"),
        ("nust gate 10", "serena hotel"),
    ]
    
    print("   Route Analysis (Normal vs Rush Hour):")
    print("   " + "-"*50)
    
    analyzed = 0
    for start_query, end_query in test_routes:
        # Find POIs matching these queries
        start_matches = city.autocomplete(start_query)
        end_matches = city.autocomplete(end_query)
        
        if not start_matches or not end_matches:
            continue
        
        start_poi = start_matches[0]['data']
        end_poi = end_matches[0]['data']
        start_name = start_matches[0]['name']
        end_name = end_matches[0]['name']
        
        start_id = city.find_nearest_node(start_poi['lat'], start_poi['lon'])
        end_id = city.find_nearest_node(end_poi['lat'], end_poi['lon'])
        
        if start_id and end_id:
            normal, rush, delay = estimate_travel_delay(city, start_id, end_id)
            if normal and rush and normal > 60:  # Only show routes > 1 min
                analyzed += 1
                delay_pct = (delay / normal * 100) if normal > 0 else 0
                
                # Truncate names for display
                start_display = format_poi_name(start_name)[:22]
                end_display = format_poi_name(end_name)[:22]
                
                print(f"\n   {start_display}")
                print(f"      -> {end_display}")
                print(f"      Normal:     {format_time_seconds(normal)}")
                print(f"      Rush Hour:  {format_time_seconds(rush)}")
                if delay > 30:  # Show delay if > 30 seconds
                    print(f"      ⚠️  Delay:   +{format_time_seconds(delay)} (+{delay_pct:.0f}%)")
                else:
                    print(f"      Delay:      Minimal (internal roads)")
                
                if analyzed >= 4:
                    break
    
    if analyzed == 0:
        print("   Could not find routes through major roads.")
        print("   Try expanding the map coverage area.")
    
    print("\n   " + "-"*50)
    print("   📝 Note: Rush hour affects PRIMARY and TRUNK roads")
    print("      (highways, main arterials). Internal campus roads")
    print("      and residential streets are less affected.")
    print("\n   💡 Rush hour typically adds 20-50% to travel time")
    print("      on routes using IJP Road, Margalla Road, etc.")
    
    input("\n   Press Enter to return...")
    toggle_traffic()

def trip_time_planner():
    """Help user plan departure/arrival times."""
    print("\n" + "="*55)
    print("   ⏰ TRIP TIME PLANNER")
    print("="*55)
    print("\n   Plan when to leave to arrive on time!")
    print()
    print("   1. Calculate 'Leave By' time (I need to arrive at X)")
    print("   2. Calculate 'Arrive By' time (I'm leaving at X)")
    print("   3. Back to Main Menu")
    print()
    
    choice = input("   Select option: ").strip()
    
    if choice == '1':
        plan_leave_by()
    elif choice == '2':
        plan_arrive_by()
    elif choice == '3':
        main_menu()
    else:
        print("   ⚠️  Invalid option")
        trip_time_planner()

def plan_leave_by():
    """Calculate when to leave to arrive by target time."""
    print("\n   --- Calculate Departure Time ---")
    print("\n   First, select your route:")
    
    # Get start location
    print("\n   Start location:")
    start_query = input("   Search: ").strip()
    if not start_query:
        trip_time_planner()
        return
    
    # Use autocomplete which returns list of dicts with 'name' and 'data' keys
    suggestions = city.autocomplete(start_query.lower())
    if not suggestions:
        print("   ⚠️  No locations found")
        trip_time_planner()
        return
    
    print("\n   Found locations:")
    for i, item in enumerate(suggestions[:5], 1):
        name = format_poi_name(item['name'])
        print(f"   {i}. {name}")
    
    try:
        start_choice = int(input("\n   Select start (number): ").strip()) - 1
        if start_choice < 0 or start_choice >= min(5, len(suggestions)):
            trip_time_planner()
            return
        start_item = suggestions[start_choice]
        start_name = start_item['name']
    except:
        trip_time_planner()
        return
    
    # Get end location
    print("\n   Destination:")
    end_query = input("   Search: ").strip()
    if not end_query:
        trip_time_planner()
        return
    
    end_suggestions = city.autocomplete(end_query.lower())
    if not end_suggestions:
        print("   ⚠️  No locations found")
        trip_time_planner()
        return
    
    print("\n   Found locations:")
    for i, item in enumerate(end_suggestions[:5], 1):
        name = format_poi_name(item['name'])
        print(f"   {i}. {name}")
    
    try:
        end_choice = int(input("\n   Select destination (number): ").strip()) - 1
        if end_choice < 0 or end_choice >= min(5, len(end_suggestions)):
            trip_time_planner()
            return
        end_item = end_suggestions[end_choice]
        end_name = end_item['name']
    except:
        trip_time_planner()
        return
    
    # Get arrival time
    print("\n   What time do you need to arrive?")
    arrival_str = input("   Enter time (HH:MM, 24hr format): ").strip()
    
    # Get POI data from the autocomplete results
    start_poi = start_item['data']
    end_poi = end_item['data']
    
    if not start_poi or not end_poi:
        print("   ⚠️  Could not find locations")
        trip_time_planner()
        return
    
    start_id = city.find_nearest_node(start_poi['lat'], start_poi['lon'])
    end_id = city.find_nearest_node(end_poi['lat'], end_poi['lon'])
    
    if not start_id or not end_id:
        print("   ⚠️  Locations not connected to road network")
        trip_time_planner()
        return
    
    # Get travel times
    normal_time, rush_time, delay = estimate_travel_delay(city, start_id, end_id)
    
    if not normal_time:
        print("   ⚠️  Could not calculate route")
        trip_time_planner()
        return
    
    # Parse arrival time and calculate departure
    try:
        target_hour, target_min = map(int, arrival_str.split(':'))
        now = datetime.now()
        arrival = now.replace(hour=target_hour, minute=target_min, second=0)
        if arrival < now:
            arrival += timedelta(days=1)
        
        # Check if route will be during rush hour
        departure_check = arrival - timedelta(seconds=rush_time)
        will_be_rush, _ = is_rush_hour(departure_check)
        
        travel_time = rush_time if will_be_rush else normal_time
        buffer = travel_time * 0.15  # 15% buffer for safety
        departure = arrival - timedelta(seconds=travel_time + buffer)
        
        print("\n" + "="*55)
        print("   📋 TRIP PLAN")
        print("="*55)
        print(f"\n   Route: {start_name}")
        print(f"       -> {end_name}")
        print(f"\n   Target Arrival: {arrival.strftime('%I:%M %p')}")
        print()
        
        if will_be_rush:
            print("   ⚠️  Your trip falls during rush hour!")
            print(f"   Expected Travel Time: {format_time_seconds(rush_time)}")
            print(f"   (Normal time would be: {format_time_seconds(normal_time)})")
        else:
            print(f"   Expected Travel Time: {format_time_seconds(normal_time)}")
        
        print(f"\n   ✅ RECOMMENDED DEPARTURE: {departure.strftime('%I:%M %p')}")
        print(f"      (includes {int(buffer/60)} min buffer)")
        
    except Exception as e:
        print(f"   ⚠️  Invalid time format. Use HH:MM (e.g., 09:00)")
    
    input("\n   Press Enter to return...")
    trip_time_planner()

def plan_arrive_by():
    """Calculate estimated arrival time when leaving at specific time."""
    print("\n   --- Calculate Arrival Time ---")
    print("\n   First, select your route:")
    
    # Get start location
    print("\n   Start location:")
    start_query = input("   Search: ").strip()
    if not start_query:
        trip_time_planner()
        return
    
    # Use autocomplete which returns list of dicts with 'name' and 'data' keys
    suggestions = city.autocomplete(start_query.lower())
    if not suggestions:
        print("   ⚠️  No locations found")
        trip_time_planner()
        return
    
    print("\n   Found locations:")
    for i, item in enumerate(suggestions[:5], 1):
        name = format_poi_name(item['name'])
        print(f"   {i}. {name}")
    
    try:
        start_choice = int(input("\n   Select start (number): ").strip()) - 1
        if start_choice < 0 or start_choice >= min(5, len(suggestions)):
            trip_time_planner()
            return
        start_item = suggestions[start_choice]
        start_name = start_item['name']
    except:
        trip_time_planner()
        return
    
    # Get end location
    print("\n   Destination:")
    end_query = input("   Search: ").strip()
    if not end_query:
        trip_time_planner()
        return
    
    end_suggestions = city.autocomplete(end_query.lower())
    if not end_suggestions:
        print("   ⚠️  No locations found")
        trip_time_planner()
        return
    
    print("\n   Found locations:")
    for i, item in enumerate(end_suggestions[:5], 1):
        name = format_poi_name(item['name'])
        print(f"   {i}. {name}")
    
    try:
        end_choice = int(input("\n   Select destination (number): ").strip()) - 1
        if end_choice < 0 or end_choice >= min(5, len(end_suggestions)):
            trip_time_planner()
            return
        end_item = end_suggestions[end_choice]
        end_name = end_item['name']
    except:
        trip_time_planner()
        return
    
    # Get departure time
    print("\n   What time are you leaving?")
    departure_str = input("   Enter time (HH:MM, 24hr format): ").strip()
    
    # Get POI data from the autocomplete results
    start_poi = start_item['data']
    end_poi = end_item['data']
    
    if not start_poi or not end_poi:
        print("   ⚠️  Could not find locations")
        trip_time_planner()
        return
    
    start_id = city.find_nearest_node(start_poi['lat'], start_poi['lon'])
    end_id = city.find_nearest_node(end_poi['lat'], end_poi['lon'])
    
    if not start_id or not end_id:
        print("   ⚠️  Locations not connected to road network")
        trip_time_planner()
        return
    
    # Get travel times
    normal_time, rush_time, delay = estimate_travel_delay(city, start_id, end_id)
    
    if not normal_time:
        print("   ⚠️  Could not calculate route")
        trip_time_planner()
        return
    
    # Parse departure time and calculate arrival
    try:
        dep_hour, dep_min = map(int, departure_str.split(':'))
        now = datetime.now()
        departure = now.replace(hour=dep_hour, minute=dep_min, second=0)
        if departure < now:
            departure += timedelta(days=1)
        
        # Check if departure is during rush hour
        will_be_rush, period = is_rush_hour(departure)
        travel_time = rush_time if will_be_rush else normal_time
        arrival = departure + timedelta(seconds=travel_time)
        
        print("\n" + "="*55)
        print("   📋 TRIP ESTIMATE")
        print("="*55)
        print(f"\n   Route: {start_name}")
        print(f"       -> {end_name}")
        print(f"\n   Departure: {departure.strftime('%I:%M %p')}")
        print()
        
        if will_be_rush:
            print(f"   ⚠️  Departing during {period}!")
            print(f"   Expected Travel Time: {format_time_seconds(rush_time)}")
            print(f"   (Normal time would be: {format_time_seconds(normal_time)})")
            if delay > 0:
                print(f"   Rush hour adds: +{format_time_seconds(delay)}")
        else:
            print(f"   Expected Travel Time: {format_time_seconds(normal_time)}")
        
        print(f"\n   ✅ ESTIMATED ARRIVAL: {arrival.strftime('%I:%M %p')}")
        
    except Exception as e:
        print(f"   ⚠️  Invalid time format. Use HH:MM (e.g., 09:00)")
    
    input("\n   Press Enter to return...")
    trip_time_planner()

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
    
    # Check real-time rush hour status
    is_rush, period = is_rush_hour()
    now = datetime.now()
    
    print("\n")
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║       🌸 NUST Intelligent Navigation System          ║")
    print("  ╠═══════════════════════════════════════════════════════╣")
    
    # Show current time and rush hour indicator
    time_str = now.strftime('%I:%M %p')
    if is_rush:
        print(f"  ║   ⏰ {time_str} | 🔴 {period} Active               ║")
    else:
        print(f"  ║   ⏰ {time_str} | ⚪ Normal Traffic                ║")
    
    print("  ╠═══════════════════════════════════════════════════════╣")
    print("  ║                                                       ║")
    print("  ║   1. 🗺️  Find Route (A* / BFS)                        ║")
    print("  ║   2. 📍 Multi-Stop Route (TSP)                        ║")
    
    # Enhanced traffic menu option
    if rush_hour_active:
        print("  ║   3. 🚦 Rush Hour Mode [🔴 ENABLED]                   ║")
    elif is_rush:
        print("  ║   3. 🚦 Rush Hour Mode [⚠️  Recommended!]             ║")
    else:
        print("  ║   3. 🚦 Rush Hour Mode [⚪ OFF]                       ║")
    
    print("  ║   4. 📜 View Trip History                             ║")
    print("  ║   5. ⏰ Trip Time Planner                              ║")
    print("  ║   6. 🚪 Exit                                          ║")
    print("  ║                                                       ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    
    # Show tip if rush hour is active but mode is off
    if is_rush and not rush_hour_active:
        print(f"\n  💡 TIP: Enable Rush Hour Mode for accurate {period} times!")
    
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
        trip_time_planner()
    elif choice == '6':
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