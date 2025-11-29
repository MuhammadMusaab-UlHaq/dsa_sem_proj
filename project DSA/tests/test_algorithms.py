import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.structures import CityGraph
from src.algorithms import a_star_search, multi_stop_route, bfs_search
import random

def get_distant_node(graph, start_node, steps=10):
    """
    Performs a random walk to find a valid node 'steps' away.
    This ensures start != end.
    """
    current = start_node
    for _ in range(steps):
        neighbors = graph.get_neighbors(current)
        if not neighbors:
            break
        # Pick a random neighbor to avoid bouncing back and forth (A->B->A)
        next_node = random.choice(neighbors)[0] 
        current = next_node
    return current

def run_test():
    # 1. Load Graph
    # Get parent directory (project root)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nodes_path = os.path.join(parent_dir, 'data', 'nodes.json')
    edges_path = os.path.join(parent_dir, 'data', 'edges.json')
    
    city = CityGraph()
    city.load_data(nodes_path, edges_path)
    
    # 2. Pick a valid Start Node (ensure it has neighbors)
    all_ids = list(city.nodes.keys())
    start_node = None
    for nid in all_ids:
        if city.get_neighbors(nid):
            start_node = nid
            break
            
    if not start_node:
        print("Error: Graph has no edges!")
        return

    # 3. Find a distant End Node (Walk 10 steps away)
    end_node = get_distant_node(city, start_node, steps=10)

    if start_node == end_node:
        print("Could not find a distant node (Graph might be too small or disconnected).")
        return

    print(f"\n--- Test 1: Basic A* (Car) ---")
    print(f"Start: {start_node} -> End: {end_node}")
    
    path, cost = a_star_search(city, start_node, end_node, mode='car')
    
    if path:
        print(f"Path Found! Steps: {len(path)}")
        print(f"Cost: {cost:.2f}")
        # Print first 5 and last 5 nodes to keep output clean
        if len(path) > 10:
            print(f"Route: {path[:3]} ... {path[-3:]}")
        else:
            print(f"Route: {path}")
    else:
        print("No path found (Nodes might be in different sub-graphs).")
        return

    print(f"\n--- Test 2: Topography Check (Walk vs Car) ---")
    path_w, cost_w = a_star_search(city, start_node, end_node, mode='walk')
    
    print(f"Car Cost:  {cost:.2f}")
    print(f"Walk Cost: {cost_w:.2f}")
    
    # Logic Check
    if cost_w > cost:
        diff = cost_w - cost
        print(f">> SUCCESS: Walking is penalized by {diff:.2f} (due to elevation/terrain).")
    elif cost_w == cost:
        print(">> NOTE: Costs are equal (Path is perfectly flat).")
    else:
        print(">> WEIRD: Walking is cheaper? Check cost function.")

    print(f"\n--- Test 3: Multi-Stop Routing ---")
    # Route: Start -> End -> Start
    stops = [start_node, end_node, start_node]
    m_path, m_cost = multi_stop_route(city, stops, mode='car')
    
    if m_path:
        print(f"Multi-stop path length: {len(m_path)}")
        print(f"Total Cost: {m_cost:.2f}")
    else:
        print("Multi-stop failed.")

        print(f"\n--- Test 4: BFS (Simplest Route) ---")
    bfs_path, bfs_hops = bfs_search(city, start_node, end_node)
    
    if bfs_path:
        print(f"BFS Path Found!")
        print(f"Total Intersections (Nodes visited): {bfs_hops}")
        if len(bfs_path) > 10:
             print(f"BFS Route: {bfs_path[:3]} ... {bfs_path[-3:]}")
        else:
             print(f"BFS Route: {bfs_path}")
    else:
        print("BFS failed to find a path.")

if __name__ == "__main__":
    run_test()