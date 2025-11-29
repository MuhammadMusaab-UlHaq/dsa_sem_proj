import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.structures import CityGraph, MinHeap

def test_graph_loading():
    print("--- Testing Graph Loading ---")
    # Get parent directory (project root)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nodes_path = os.path.join(parent_dir, 'data', 'nodes.json')
    edges_path = os.path.join(parent_dir, 'data', 'edges.json')
    
    city = CityGraph()
    city.load_data(nodes_path, edges_path)
    
    # Check if we have nodes
    total_nodes = len(city.nodes)
    print(f"Graph Nodes: {total_nodes}")
    
    if total_nodes > 0:
        first_node_id = list(city.nodes.keys())[0]
        print(f"Sample Node {first_node_id}: {city.get_node(first_node_id)}")
        print(f"Neighbors: {city.get_neighbors(first_node_id)}")
    
    # Test Spatial Hashing
    print("\n--- Testing POI Search ---")
    # Pick a random node's location
    sample_node = city.get_node(list(city.nodes.keys())[100]) 
    pois = city.spatial.get_nearby(sample_node['lat'], sample_node['lon'])
    print(f"POIs near Node 100: {pois}")

def test_heap():
    print("\n--- Testing MinHeap Implementation ---")
    pq = MinHeap()
    pq.push((10, 'A'))
    pq.push((5, 'B'))
    pq.push((20, 'C'))
    pq.push((2, 'D')) # Smallest
    
    print("Popping items (should be 2, 5, 10, 20):")
    while not pq.is_empty():
        print(pq.pop())

if __name__ == "__main__":
    test_graph_loading()
    test_heap()