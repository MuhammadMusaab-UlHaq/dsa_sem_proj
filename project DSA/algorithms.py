import math
from collections import deque
from structures import MinHeap

METERS_PER_DEG_LAT = 111000
METERS_PER_DEG_LON = 93000 

# STRICT ADMISSIBILITY CONSTANTS
MAX_CAR_SPEED = 34.0 
MAX_WALK_SPEED = 2.0 

def get_distance_meters(node_a, node_b):
    d_lat = (node_a['lat'] - node_b['lat']) * METERS_PER_DEG_LAT
    d_lon = (node_a['lon'] - node_b['lon']) * METERS_PER_DEG_LON
    return math.sqrt(d_lat**2 + d_lon**2)

def heuristic_time(node_a, node_b, mode='car'):
    dist = get_distance_meters(node_a, node_b)
    if mode == 'car':
        return dist / MAX_CAR_SPEED
    else:
        return dist / MAX_WALK_SPEED

def get_tobler_time(dist, elev_diff):
    if dist == 0: return 0
    slope = elev_diff / dist
    # Tobler's Hiking Function
    speed_kmh = 6 * math.exp(-3.5 * abs(slope + 0.05))
    speed_ms = speed_kmh / 3.6
    return dist / speed_ms

def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from and came_from[current] is not None:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]


# BFS IMPLEMENTATION ---
def bfs_search(graph, start, end):
    """
    Breadth-First Search to find the path with the fewest number of nodes/intersections.
    Ignores physical distance and edge weights.
    Returns: (path, number_of_turns)
    """
    if start not in graph.nodes or end not in graph.nodes:
        return None, 0

    # queue stores: (current_node)
    queue = deque([start])
    
    # visited stores: {child: parent} for path reconstruction
    # The start node has no parent (None)
    visited = {start: None}

    while queue:
        current = queue.popleft()

        if current == end:
            # Reconstruct path
            path = reconstruct_path(visited, end)
            # Returns path and total turns (path length - 1)
            return path, len(path) - 1

        # Iterate neighbors
        neighbors = graph.get_neighbors(current)
        for neighbor_data in neighbors:
            # neighbor_data is tuple: (id, dist, walk, drive, geom, type)
            neighbor_id = neighbor_data[0]

            if neighbor_id not in visited:
                visited[neighbor_id] = current
                queue.append(neighbor_id)
                
    return None, 0

def a_star_search(graph, start_id, end_id, mode='car'):
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

        # --- FIX IS HERE ---
        # We now unpack 6 values. The last two are geometry and highway_type, which we ignore with _
        neighbors = graph.get_neighbors(current_id)
        for neighbor_data in neighbors:
            # Safe unpacking for variable length tuples (Robustness)
            neighbor_id = neighbor_data[0]
            dist = neighbor_data[1]
            is_walk = neighbor_data[2]
            is_drive = neighbor_data[3]
            # indices 4 and 5 are geometry and highway_type, ignored here
            
            if mode == 'car' and not is_drive: continue
            if mode == 'walk' and not is_walk: continue
            
            curr_node = graph.nodes[current_id]
            neigh_node = graph.nodes[neighbor_id]
            ele_diff = neigh_node['ele'] - curr_node['ele']
            
            if mode == 'walk':
                edge_cost = get_tobler_time(dist, ele_diff)
            else:
                base_speed = 11.1 
                slope = ele_diff / dist if dist > 0 else 0
                
                if slope > 0.05: speed = base_speed * 0.8
                elif slope < -0.05: speed = base_speed * 1.1
                else: speed = base_speed
                
                edge_cost = dist / speed
            
            tentative_g = g_score[current_id] + edge_cost

            if tentative_g < g_score[neighbor_id]:
                came_from[neighbor_id] = current_id
                g_score[neighbor_id] = tentative_g
                f = tentative_g + heuristic_time(graph.nodes[neighbor_id], graph.nodes[end_id], mode)
                f_score[neighbor_id] = f
                open_set.push((f, neighbor_id))

    return None, float('inf') 

def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]

def multi_stop_route(graph, stops, mode='car'):
    full_path = []
    total_cost = 0
    for i in range(len(stops) - 1):
        start = stops[i]
        end = stops[i+1]
        segment_path, segment_cost = a_star_search(graph, start, end, mode)
        if not segment_path: return None, float('inf')
        if i > 0: full_path.extend(segment_path[1:])
        else: full_path.extend(segment_path)
        total_cost += segment_cost
    return full_path, total_cost