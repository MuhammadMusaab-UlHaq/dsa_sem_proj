import json
import math

class MinHeap:
    """
    A manual implementation of a Min-Priority Queue using a Binary Heap.
    Used for A* to efficiently retrieve the node with the lowest F-score.
    """
    def __init__(self):
        # Array to store heap elements: (f_score, node_id)
        self.heap = []

    def push(self, item):
        """Inserts an item (cost, node_id) and sifts it up."""
        self.heap.append(item)
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        """Removes and returns the smallest item."""
        if not self.heap:
            return None
        
        # Swap root with last element
        root = self.heap[0]
        last = self.heap.pop()
        
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
            
        return root

    def is_empty(self):
        return len(self.heap) == 0

    def _sift_up(self, index):
        parent_idx = (index - 1) // 2
        if index > 0 and self.heap[index][0] < self.heap[parent_idx][0]:
            # Swap if child is smaller than parent
            self.heap[index], self.heap[parent_idx] = self.heap[parent_idx], self.heap[index]
            self._sift_up(parent_idx)

    def _sift_down(self, index):
        smallest = index
        left = 2 * index + 1
        right = 2 * index + 2

        if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]:
            smallest = left
        
        if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]:
            smallest = right
            
        if smallest != index:
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self._sift_down(smallest)

class SpatialGrid:
    """
    Implements Spatial Hashing to find POIs (Fuel Stations) in O(1) time.
    Instead of checking 1000 nodes, we only check the specific grid cell.
    """
    def __init__(self, cell_size=0.005): # 0.005 deg is roughly 500m
        self.cell_size = cell_size
        self.grid = {} # Key: (x, y), Value: [List of Node IDs]

    def _get_key(self, lat, lon):
        return (int(lat / self.cell_size), int(lon / self.cell_size))

    def add_poi(self, node_id, lat, lon, type_tag):
        key = self._get_key(lat, lon)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append({'id': node_id, 'lat': lat, 'lon': lon, 'type': type_tag})

    def get_nearby(self, lat, lon):
        """Returns POIs in the same grid cell."""
        key = self._get_key(lat, lon)
        return self.grid.get(key, [])

class CityGraph:
    """
    The Graph Data Structure (Adjacency List).
    """
    def __init__(self):
        self.nodes = {}   # { node_id: {lat, lon, elevation} }
        self.adj_list = {} # { node_id: [ (neighbor_id, weight, is_walkable, is_drivable) ] }
        self.spatial = SpatialGrid()

    def load_data(self, nodes_file, edges_file):
        print("Loading graph data...")
        
        # 1. Load Nodes
        with open(nodes_file, 'r') as f:
            nodes_data = json.load(f)
            
        for n_id, data in nodes_data.items():
            # JSON keys are strings, convert back to int for consistency
            node_id = int(n_id) 
            self.nodes[node_id] = {
                'lat': data['lat'],
                'lon': data['lon'],
                'ele': data.get('elevation', 0)
            }
            self.adj_list[node_id] = [] # Initialize adjacency list
            
            # Add to spatial grid if it looks like a POI (simulation for project)
            # For demo, we'll pretend every 50th node is a "Fuel Station"
            if node_id % 50 == 0:
                self.spatial.add_poi(node_id, data['lat'], data['lon'], "Fuel Station")

        # 2. Load Edges
        with open(edges_file, 'r') as f:
            edges_data = json.load(f)
            
        count = 0
        for edge in edges_data:
            u, v = int(edge['u']), int(edge['v'])
            
            # Verify nodes exist (data safety)
            if u in self.nodes and v in self.nodes:
                # Store tuple: (neighbor, distance_meters, walk_allowed, car_allowed)
                self.adj_list[u].append((
                    v, 
                    edge['weight'], 
                    edge['is_walkable'], 
                    edge['is_drivable']
                ))
                count += 1
                
        print(f"Successfully loaded {len(self.nodes)} nodes and {count} edges.")
        
    def get_neighbors(self, node_id):
        return self.adj_list.get(node_id, [])
        
    def get_node(self, node_id):
        return self.nodes.get(node_id)