import math
from itertools import permutations
from collections import deque
from structures import MinHeap

METERS_PER_DEG_LAT = 111000
METERS_PER_DEG_LON = 93000

# STRICT ADMISSIBILITY CONSTANTS
MAX_CAR_SPEED = 34.0
MAX_WALK_SPEED = 2.0

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
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]

# ================= A* SEARCH =================
def a_star_search(graph, start_id, end_id, mode='car'):
    """
    A* pathfinding algorithm with topology awareness.
    Returns: (path, cost) or (None, inf) if no path found.
    """
    open_set = MinHeap()
    open_set.push((0, start_id))
    came_from = {}
    
    g_score = {node_id: float('inf') for node_id in graph.nodes}
    g_score[start_id] = 0
    
    f_score = {node_id: float('inf') for node_id in graph.nodes}
    f_score[start_id] = heuristic_time(graph.nodes[start_id], graph.nodes[end_id], mode)

    while not open_set.is_empty():
        current_f, current_id = open_set.pop()
        
        if current_id == end_id:
            return reconstruct_path(came_from, current_id), g_score[end_id]

        neighbors = graph.get_neighbors(current_id)
        for neighbor_data in neighbors:
            neighbor_id = neighbor_data[0]
            dist = neighbor_data[1]
            is_walk = neighbor_data[2]
            is_drive = neighbor_data[3]
            
            # Skip infinity weight edges (penalized)
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
                base_speed = 11.1
                slope = ele_diff / dist if dist > 0 else 0
                
                if slope > 0.05:
                    speed = base_speed * 0.8
                elif slope < -0.05:
                    speed = base_speed * 1.1
                else:
                    speed = base_speed
                
                edge_cost = dist / speed
            
            tentative_g = g_score[current_id] + edge_cost

            if tentative_g < g_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = tentative_g
                f = tentative_g + heuristic_time(graph.nodes[neighbor_id], graph.nodes[end_id], mode)
                f_score[neighbor_id] = f
                open_set.push((f, neighbor_id))

    return None, float('inf')

# ================= BFS SEARCH (Farida) =================
def bfs_search(graph, start, end):
    """
    Breadth-First Search to find the path with fewest intersections.
    Ignores physical distance and edge weights.
    Returns: (path, number_of_turns)
    """
    if start not in graph.nodes or end not in graph.nodes:
        return None, 0

    queue = deque([start])
    visited = {start: None}

    while queue:
        current = queue.popleft()

        if current == end:
            path = reconstruct_path(visited, end)
            return path, len(path) - 1

        neighbors = graph.get_neighbors(current)
        for neighbor_data in neighbors:
            neighbor_id = neighbor_data[0]

            if neighbor_id not in visited:
                visited[neighbor_id] = current
                queue.append(neighbor_id)
                
    return None, 0

# ================= K-SHORTEST PATHS (Ahmed) =================
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
    Finds top k distinct routes by iteratively penalizing used edges.
    """
    found_paths = []
    penalized_edges = []

    for _ in range(k):
        path, cost = a_star_search(graph, start_id, end_id, mode)
        
        if not path:
            break
            
        found_paths.append((path, cost))
        
        # Penalize edges in this path
        for j in range(len(path) - 1):
            u, v = path[j], path[j+1]
            old_w = _modify_edge_weight(graph, u, v, float('inf'))
            if old_w is not None:
                penalized_edges.append((u, v, old_w))
                
                old_w_rev = _modify_edge_weight(graph, v, u, float('inf'))
                if old_w_rev is not None:
                    penalized_edges.append((v, u, old_w_rev))

    # Restore graph state
    for u, v, original_weight in penalized_edges:
        _modify_edge_weight(graph, u, v, original_weight)
        
    return found_paths

# ================= TRAFFIC SIMULATION (Ahmed) =================
def simulate_traffic(graph):
    """
    Simulate rush hour by slowing down major roads.
    Returns list of modifications for resetting.
    """
    modifications = []
    
    print("🚦 Applying Traffic Delays...")
    for u, edges in graph.adj_list.items():
        for edge in edges:
            v = edge[0]
            weight = edge[1]
            highway_type = edge[5] if len(edge) > 5 else ''
            
            if highway_type in ['primary', 'trunk', 'primary_link', 'trunk_link']:
                new_weight = weight * 3.0
                _modify_edge_weight(graph, u, v, new_weight)
                modifications.append((u, v, weight))
    
    return modifications

def reset_traffic(graph, modifications):
    """Resets the graph weights back to normal."""
    for u, v, original_weight in modifications:
        _modify_edge_weight(graph, u, v, original_weight)
    print("🚦 Traffic cleared.")

# ================= TSP OPTIMIZATION (Usman) =================
def optimize_route_order(graph, start, list_of_stops, mode='car'):
    """
    TSP Approximation - Finds optimal visiting order for multiple stops.
    Uses brute-force permutation for small number of stops (2-6).
    
    Returns: (best_order, total_cost, segment_paths)
    """
    if not list_of_stops:
        return [], 0, {}
    
    all_permutations = list(permutations(list_of_stops))
    
    best_order = None
    best_total_cost = float('inf')
    best_segments = {}
    
    print(f"\n🔄 Evaluating {len(all_permutations)} possible route orders...")
    
    for perm in all_permutations:
        full_route = [start] + list(perm)
        total_cost = 0
        segments = {}
        valid_route = True
        
        for i in range(len(full_route) - 1):
            from_node = full_route[i]
            to_node = full_route[i + 1]
            
            path, cost = a_star_search(graph, from_node, to_node, mode)
            
            if not path:
                valid_route = False
                break
            
            total_cost += cost
            segments[(from_node, to_node)] = path
        
        if valid_route and total_cost < best_total_cost:
            best_total_cost = total_cost
            best_order = list(perm)
            best_segments = segments.copy()
    
    if best_order is None:
        print("❌ No valid route found for these stops")
        return [], float('inf'), {}
    
    print(f"✅ Found optimal route! Total time: {best_total_cost/60:.1f} minutes")
    
    return best_order, best_total_cost, best_segments

# ================= MULTI-STOP ROUTE =================
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