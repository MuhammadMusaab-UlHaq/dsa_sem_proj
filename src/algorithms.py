import math
from itertools import permutations
from collections import deque
from structures import MinHeap

METERS_PER_DEG_LAT = 111000
METERS_PER_DEG_LON = 93000

# STRICT ADMISSIBILITY CONSTANTS
# These are MAXIMUM speed, heuristic must never overestimate
MAX_CAR_SPEED = 25.0   
MAX_WALK_SPEED = 1.8   

def get_distance_meters(node_a, node_b):
    """Calculate distance between two nodes in meters."""
    d_lat = (node_a['lat'] - node_b['lat']) * METERS_PER_DEG_LAT
    d_lon = (node_a['lon'] - node_b['lon']) * METERS_PER_DEG_LON
    return math.sqrt(d_lat**2 + d_lon**2)

def heuristic_time(node_a, node_b, mode='car'):
    """Heuristic function for A* - estimated time to reach goal."""
    dist = get_distance_meters(node_a, node_b)
    if mode == 'car':
        return dist / MAX_CAR_SPEED
    else:
        return dist / MAX_WALK_SPEED

def get_tobler_time(dist, elev_diff):
    """Tobler's Hiking Function for walking speed based on slope."""
    if dist == 0:
        return 0
    slope = elev_diff / dist
    speed_kmh = 6 * math.exp(-3.5 * abs(slope + 0.05))
    speed_ms = speed_kmh / 3.6
    return dist / speed_ms

def reconstruct_path(came_from, current):
    """Reconstruct path from A* search result."""
    total_path = [current]
    while current in came_from and came_from[current] is not None:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]

#  A* SEARCH 

def a_star_search(graph, start_id, end_id, mode='car', return_stats=False):
    """
    A* pathfinding algorithm with topology awareness.
    Returns: (path, cost) or (path, cost, stats) if return_stats=True
    """
    import time
    start_time = time.time()
    
    # Validate inputs
    if start_id is None or end_id is None:
        if return_stats:
            return None, float('inf'), {'algorithm_name': 'A*', 'nodes_explored': 0, 'heap_operations': 0, 'time_ms': 0}
        return None, float('inf')
    
    if start_id not in graph.nodes or end_id not in graph.nodes:
        if return_stats:
            return None, float('inf'), {'algorithm_name': 'A*', 'nodes_explored': 0, 'heap_operations': 0, 'time_ms': 0}
        return None, float('inf')
    
    open_set = MinHeap()
    open_set.push((0, start_id))
    came_from = {}
    
    g_score = {node_id: float('inf') for node_id in graph.nodes}
    g_score[start_id] = 0
    
    f_score = {node_id: float('inf') for node_id in graph.nodes}
    f_score[start_id] = heuristic_time(graph.nodes[start_id], graph.nodes[end_id], mode)

    nodes_explored = 0
    heap_operations = 1  # Initial push

    while not open_set.is_empty():
        current_f, current_id = open_set.pop()
        heap_operations += 1
        nodes_explored += 1
        
        if current_id == end_id:
            elapsed_ms = (time.time() - start_time) * 1000
            path = reconstruct_path(came_from, current_id)
            cost = g_score[end_id]
            
            if return_stats:
                stats = {
                    'algorithm_name': 'A* Search',
                    'nodes_explored': nodes_explored,
                    'heap_operations': heap_operations,
                    'time_ms': elapsed_ms
                }
                return path, cost, stats
            return path, cost

        neighbors = graph.get_neighbors(current_id)
        for neighbor_data in neighbors:
            neighbor_id = neighbor_data[0]
            dist = neighbor_data[1]
            is_walk = neighbor_data[2]
            is_drive = neighbor_data[3]
            
            if dist == float('inf'):
                continue

            if mode == 'car' and not is_drive:
                continue
            if mode == 'walk' and not is_walk:
                continue
            
            curr_node = graph.nodes[current_id]
            neigh_node = graph.nodes[neighbor_id]
            ele_diff = neigh_node.get('ele', 0) - curr_node.get('ele', 0)
            
            if mode == 'walk':
                edge_cost = get_tobler_time(dist, ele_diff)
            else:
                highway_type = neighbor_data[5] if len(neighbor_data) > 5 else ''
                
                speed_map = {
                    'motorway': 25.0,       
                    'motorway_link': 19.4,  
                    'trunk': 19.4,          
                    'trunk_link': 16.7,     
                    'primary': 13.9,        
                    'primary_link': 11.1,   
                    'secondary': 11.1,      
                    'secondary_link': 9.7,  
                    'tertiary': 9.7,        
                    'tertiary_link': 8.3,  
                    'residential': 8.3,     
                    'living_street': 5.6,   
                    'service': 5.6,         
                    'unclassified': 8.3,    
                }
                
                base_speed = speed_map.get(highway_type, 8.3)  
                
                # Apply rush hour penalty if active
                if getattr(graph, 'rush_hour_active', False):
                    rush_multiplier = RUSH_HOUR_MULTIPLIERS.get(highway_type, 1.0)
                    base_speed = base_speed / rush_multiplier  # Slower speed
                
                # Slope adjustment (mild effect)
                slope = ele_diff / dist if dist > 0 else 0
                if slope > 0.05:
                    speed = base_speed * 0.92  # Slight uphill penalty
                elif slope < -0.05:
                    speed = base_speed * 1.03  # Slight downhill boost
                else:
                    speed = base_speed
                
                # Intersection delay - only on roads likely to have traffic lights
                # Much reduced: ~2 sec per 500m on major roads only
                if getattr(graph, 'rush_hour_active', False):
                    if highway_type in ['primary', 'secondary', 'trunk']:
                        intersection_delay = (dist / 500) * 4  # 4 sec per 500m during rush
                    else:
                        intersection_delay = 0
                else:
                    if highway_type in ['primary', 'secondary', 'trunk']:
                        intersection_delay = (dist / 500) * 2  # 2 sec per 500m normal
                    else:
                        intersection_delay = 0
                
                edge_cost = (dist / speed) + intersection_delay
            
            tentative_g = g_score[current_id] + edge_cost

            if tentative_g < g_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = tentative_g
                f = tentative_g + heuristic_time(graph.nodes[neighbor_id], graph.nodes[end_id], mode)
                f_score[neighbor_id] = f
                open_set.push((f, neighbor_id))
                heap_operations += 1

    if return_stats:
        return None, float('inf'), {'algorithm_name': 'A*', 'nodes_explored': nodes_explored, 'heap_operations': heap_operations, 'time_ms': 0}
    return None, float('inf')



#  BFS SEARCH (Farida) 
def bfs_search(graph, start, end, return_stats=False):
    """
    Breadth-First Search for path with fewest intersections.
    """
    import time
    start_time = time.time()
    
    if start not in graph.nodes or end not in graph.nodes:
        if return_stats:
            return None, 0, {'algorithm_name': 'BFS', 'nodes_explored': 0, 'heap_operations': 0, 'time_ms': 0}
        return None, 0

    queue = deque([start])
    visited = {start: None}
    nodes_explored = 0

    while queue:
        current = queue.popleft()
        nodes_explored += 1

        if current == end:
            path = reconstruct_path(visited, end)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if return_stats:
                stats = {
                    'algorithm_name': 'BFS (Fewest Turns)',
                    'nodes_explored': nodes_explored,
                    'heap_operations': 0,  # BFS doesn't use heap
                    'time_ms': elapsed_ms
                }
                return path, len(path) - 1, stats
            return path, len(path) - 1

        neighbors = graph.get_neighbors(current)
        for neighbor_data in neighbors:
            neighbor_id = neighbor_data[0]

            if neighbor_id not in visited:
                visited[neighbor_id] = current
                queue.append(neighbor_id)
    
    if return_stats:
        return None, 0, {'algorithm_name': 'BFS', 'nodes_explored': nodes_explored, 'heap_operations': 0, 'time_ms': 0}
    return None, 0

#  K-SHORTEST PATHS (Ahmed) 
def _modify_edge_weight(graph, u, v, new_weight):
    """Helper to modify edge weight in adj_list."""
    if u not in graph.adj_list:
        return None

    neighbors = graph.adj_list[u]
    for i, data in enumerate(neighbors):
        if data[0] == v:
            new_tuple = (data[0], new_weight, data[2], data[3], data[4], data[5])
            graph.adj_list[u][i] = new_tuple
            return data[1]
    return None

def get_k_shortest_paths(graph, start_id, end_id, k=3, mode='car'):
    """
    Finds top k distinct routes using Yen's algorithm variant.
    Uses edge penalization to encourage route diversity.
    """
    found_paths = []
    penalized_edges = []
    seen_path_signatures = set()

    for iteration in range(k):
        path, cost = a_star_search(graph, start_id, end_id, mode)
        
        if not path:
            break
        
        # Create a signature to check for duplicate paths
        path_sig = tuple(path[::max(1, len(path)//10)])  # Sample every ~10% of nodes
        
        if path_sig in seen_path_signatures:
            # Path is too similar, try harder penalty
            for j in range(len(path) - 1):
                u, v = path[j], path[j+1]
                old_w = _modify_edge_weight(graph, u, v, float('inf'))
                if old_w is not None and old_w != float('inf'):
                    penalized_edges.append((u, v, old_w))
            continue
            
        seen_path_signatures.add(path_sig)
        found_paths.append((path, cost))
        
        # Penalize edges in this path - use multiplier instead of inf for first pass
        # This encourages alternatives while not completely blocking
        penalty_multiplier = 10.0 if iteration == 0 else float('inf')
        
        for j in range(len(path) - 1):
            u, v = path[j], path[j+1]
            current_weight = None
            
            # Get current weight
            if u in graph.adj_list:
                for data in graph.adj_list[u]:
                    if data[0] == v:
                        current_weight = data[1]
                        break
            
            if current_weight is not None and current_weight != float('inf'):
                new_weight = current_weight * penalty_multiplier if penalty_multiplier != float('inf') else float('inf')
                old_w = _modify_edge_weight(graph, u, v, new_weight)
                if old_w is not None:
                    penalized_edges.append((u, v, old_w))
                    
                    # Also penalize reverse direction
                    old_w_rev = _modify_edge_weight(graph, v, u, new_weight)
                    if old_w_rev is not None:
                        penalized_edges.append((v, u, old_w_rev))

    # Restore graph state
    for u, v, original_weight in penalized_edges:
        _modify_edge_weight(graph, u, v, original_weight)
        
    return found_paths

#  TRAFFIC SIMULATION (Ahmed) 
# Traffic multipliers for rush hour
RUSH_HOUR_MULTIPLIERS = {
    'motorway': 1.5,       
    'motorway_link': 1.6,
    'trunk': 2.0,          
    'trunk_link': 2.0,
    'primary': 1.8,        
    'primary_link': 1.7,
    'secondary': 1.5,     
    'secondary_link': 1.4,
    'tertiary': 1.3,       
    'residential': 1.1,  
}

def simulate_traffic(graph):
    """
    Simulate rush hour by marking graph for traffic mode.
    The actual slowdown is applied in A* based on road type.
    """
    print(" Applying Traffic Delays...")
    graph.rush_hour_active = True
    return []

def reset_traffic(graph, modifications=None):
    """Resets the graph to normal traffic mode."""
    graph.rush_hour_active = False
    print(" Traffic cleared.")

#  TSP OPTIMIZATION (Usman) 
def _nearest_neighbor_tsp(graph, start, stops, mode):
    """
    Greedy Nearest Neighbor heuristic for TSP.
    O(n²) - much faster than brute force for larger stop counts.
    """
    unvisited = list(stops)
    route = []
    current = start
    total_cost = 0
    segments = {}
    
    while unvisited:
        best_next = None
        best_cost = float('inf')
        best_path = None
        
        for candidate in unvisited:
            path, cost = a_star_search(graph, current, candidate, mode)
            if path and cost < best_cost:
                best_cost = cost
                best_next = candidate
                best_path = path
        
        if best_next is None:
            return None, float('inf'), {}
        
        route.append(best_next)
        segments[(current, best_next)] = best_path
        total_cost += best_cost
        current = best_next
        unvisited.remove(best_next)
    
    return route, total_cost, segments


def optimize_route_order(graph, start, list_of_stops, mode='car'):
    """
    TSP Approximation - Finds optimal visiting order for multiple stops.
    Uses brute-force for ≤4 stops, Nearest Neighbor heuristic for more.
    
    Returns: (best_order, total_cost, segment_paths, algo_stats)
    """
    import time as time_module
    start_time = time_module.time()
    
    if not list_of_stops:
        return [], 0, {}, {'algorithm_name': 'TSP', 'nodes_explored': 0, 'heap_operations': 0, 'time_ms': 0, 'permutations_checked': 0}
    
    n_stops = len(list_of_stops)
    total_nodes_explored = 0
    total_heap_ops = 0
    total_a_star_calls = 0
    
    # Use Nearest Neighbor for larger stop counts (faster)
    if n_stops > 4:
        print(f"\n Using Nearest Neighbor heuristic for {n_stops} stops...")
        order, cost, segments, nn_stats = _nearest_neighbor_tsp_with_stats(graph, start, list_of_stops, mode)
        elapsed_ms = (time_module.time() - start_time) * 1000
        
        if order:
            print(f" Found efficient route! Total time: {cost/60:.1f} minutes")
        else:
            print(" No valid route found for these stops")
        
        algo_stats = {
            'algorithm_name': f'TSP (Nearest Neighbor, {n_stops} stops)',
            'nodes_explored': nn_stats['nodes_explored'],
            'heap_operations': nn_stats['heap_operations'],
            'time_ms': elapsed_ms,
            'a_star_calls': nn_stats['a_star_calls']
        }
        return order or [], cost, segments, algo_stats
    
    # Brute force for small number of stops
    all_permutations = list(permutations(list_of_stops))
    
    best_order = None
    best_total_cost = float('inf')
    best_segments = {}
    
    print(f"\n Evaluating {len(all_permutations)} possible route orders...")
    
    for perm in all_permutations:
        full_route = [start] + list(perm)
        total_cost = 0
        segments = {}
        valid_route = True
        
        for i in range(len(full_route) - 1):
            from_node = full_route[i]
            to_node = full_route[i + 1]
            
            path, cost, stats = a_star_search(graph, from_node, to_node, mode, return_stats=True)
            total_a_star_calls += 1
            total_nodes_explored += stats['nodes_explored']
            total_heap_ops += stats['heap_operations']
            
            if not path:
                valid_route = False
                break
            
            total_cost += cost
            segments[(from_node, to_node)] = path
        
        if valid_route and total_cost < best_total_cost:
            best_total_cost = total_cost
            best_order = list(perm)
            best_segments = segments.copy()
    
    elapsed_ms = (time_module.time() - start_time) * 1000
    
    if best_order is None:
        print(" No valid route found for these stops")
        algo_stats = {
            'algorithm_name': f'TSP (Brute Force, {n_stops} stops)',
            'nodes_explored': total_nodes_explored,
            'heap_operations': total_heap_ops,
            'time_ms': elapsed_ms,
            'permutations_checked': len(all_permutations),
            'a_star_calls': total_a_star_calls
        }
        return [], float('inf'), {}, algo_stats
    
    print(f" Found optimal route! Total time: {best_total_cost/60:.1f} minutes")
    
    algo_stats = {
        'algorithm_name': f'TSP (Brute Force, {n_stops} stops)',
        'nodes_explored': total_nodes_explored,
        'heap_operations': total_heap_ops,
        'time_ms': elapsed_ms,
        'permutations_checked': len(all_permutations),
        'a_star_calls': total_a_star_calls
    }
    
    return best_order, best_total_cost, best_segments, algo_stats


def _nearest_neighbor_tsp_with_stats(graph, start, stops, mode):
    """Nearest Neighbor TSP with stats tracking."""
    unvisited = list(stops)
    route = []
    current = start
    total_cost = 0
    segments = {}
    
    total_nodes_explored = 0
    total_heap_ops = 0
    a_star_calls = 0
    
    while unvisited:
        best_next = None
        best_cost = float('inf')
        best_path = None
        
        for candidate in unvisited:
            path, cost, stats = a_star_search(graph, current, candidate, mode, return_stats=True)
            a_star_calls += 1
            total_nodes_explored += stats['nodes_explored']
            total_heap_ops += stats['heap_operations']
            
            if path and cost < best_cost:
                best_cost = cost
                best_next = candidate
                best_path = path
        
        if best_next is None:
            return None, float('inf'), {}, {'nodes_explored': total_nodes_explored, 'heap_operations': total_heap_ops, 'a_star_calls': a_star_calls}
        
        route.append(best_next)
        segments[(current, best_next)] = best_path
        total_cost += best_cost
        current = best_next
        unvisited.remove(best_next)
    
    stats = {
        'nodes_explored': total_nodes_explored,
        'heap_operations': total_heap_ops,
        'a_star_calls': a_star_calls
    }
    return route, total_cost, segments, stats

#  MULTI-STOP ROUTE 
def multi_stop_route(graph, stops, mode='car'):
    """Calculate route through multiple stops in given order."""
    full_path = []
    total_cost = 0
    for i in range(len(stops) - 1):
        start = stops[i]
        end = stops[i+1]
        segment_path, segment_cost = a_star_search(graph, start, end, mode)
        if not segment_path:
            return None, float('inf')
        if i > 0:
            full_path.extend(segment_path[1:])
        else:
            full_path.extend(segment_path)
        total_cost += segment_cost
    return full_path, total_cost