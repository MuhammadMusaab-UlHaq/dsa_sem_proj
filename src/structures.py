import json

class TrieNode:
    """Node in the Trie structure for efficient prefix searching"""
    def __init__(self):
        self.children = {}  # Dictionary: char -> TrieNode
        self.is_end_of_word = False
        self.poi_data = None  # Store complete POI info when word ends

class Trie:
    """Trie data structure for autocomplete suggestions"""
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word, poi_data=None):
        """
        Insert a word into the Trie
        Args:
            word (str): POI name to insert
            poi_data (dict): Full POI information (coordinates, type, etc.)
        """
        node = self.root
        word = word.lower()  # Case-insensitive search
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.poi_data = poi_data
    
    def search_prefix(self, prefix):
        """
        Find all words with given prefix
        Args:
            prefix (str): Search prefix (e.g., "conc")
        Returns:
            list: All matching POI names with their data
        """
        prefix = prefix.lower()
        node = self.root
        
        # Navigate to prefix end
        for char in prefix:
            if char not in node.children:
                return []  # Prefix not found
            node = node.children[char]
        
        # Collect all words from this point
        suggestions = []
        self._collect_words(node, prefix, suggestions)
        return suggestions[:10]  # Return top 10 suggestions
    
    def _collect_words(self, node, current_word, suggestions):
        """
        Recursively collect all complete words from current node
        Args:
            node (TrieNode): Current node in traversal
            current_word (str): Word built so far
            suggestions (list): Accumulator for results
        """
        if node.is_end_of_word:
            suggestions.append({
                'name': current_word,
                'data': node.poi_data
            })
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, current_word + char, suggestions)

class MinHeap:
    def __init__(self): self.heap = []
    def push(self, item):
        self.heap.append(item)
        self._sift_up(len(self.heap) - 1)
    def pop(self):
        if not self.heap: return None
        root = self.heap[0]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return root
    def is_empty(self): return len(self.heap) == 0
    def _sift_up(self, index):
        parent_idx = (index - 1) // 2
        if index > 0 and self.heap[index][0] < self.heap[parent_idx][0]:
            self.heap[index], self.heap[parent_idx] = self.heap[parent_idx], self.heap[index]
            self._sift_up(parent_idx)
    def _sift_down(self, index):
        smallest = index
        left = 2 * index + 1
        right = 2 * index + 2
        if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]: smallest = left
        if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]: smallest = right
        if smallest != index:
            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            self._sift_down(smallest)

class SpatialGrid:
    def __init__(self, cell_size=0.005): 
        self.cell_size = cell_size
        self.grid = {} 
    def add_poi(self, name, lat, lon, type_tag):
        key = (int(lat/self.cell_size), int(lon/self.cell_size))
        if key not in self.grid: self.grid[key] = []
        self.grid[key].append({'name': name, 'lat': lat, 'lon': lon, 'type': type_tag})
    def get_nearby(self, lat, lon):
        ck = (int(lat/self.cell_size), int(lon/self.cell_size))
        nearby = []
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                k = (ck[0]+dx, ck[1]+dy)
                if k in self.grid: nearby.extend(self.grid[k])
        return nearby

class CityGraph:
    def __init__(self):
        self.nodes = {}   
        self.adj_list = {} 
        self.spatial = SpatialGrid()
        self.drive_nodes = set()
        self.walk_nodes = set()
        self.pois = []
        self.poi_trie = Trie()  # Trie for POI autocomplete 

    def load_data(self, nodes_file, edges_file, pois_file="pois.json"):
        print("Loading graph data...")
        with open(nodes_file, 'r') as f:
            nodes_data = json.load(f)
        for n_id, data in nodes_data.items():
            node_id = int(n_id) 
            self.nodes[node_id] = {'lat': data['lat'], 'lon': data['lon'], 'ele': data.get('elevation', 0)}
            self.adj_list[node_id] = [] 

        with open(edges_file, 'r') as f:
            edges_data = json.load(f)
        for edge in edges_data:
            u, v = int(edge['u']), int(edge['v'])
            if u in self.nodes and v in self.nodes:
                # Store highway type in the tuple for later checking
                # (v, weight, is_walk, is_drive, geometry, highway_type)
                self.adj_list[u].append((v, edge['weight'], edge['is_walkable'], edge['is_drivable'], edge['geometry'], edge.get('highway', '')))
                
                if edge['is_drivable']:
                    self.drive_nodes.add(u); self.drive_nodes.add(v)
                if edge['is_walkable']:
                    self.walk_nodes.add(u); self.walk_nodes.add(v)
        
        try:
            with open(pois_file, 'r', encoding='utf-8') as f: 
                self.pois = json.load(f)
            
            print(f"🔍 Loading {len(self.pois)} POIs into search index...")
            for p in self.pois:
                self.spatial.add_poi(p['name'], p['lat'], p['lon'], p['type'])
                # Insert POI into Trie for autocomplete
                self.poi_trie.insert(p['name'], p)
            
            print(f"✅ Search index ready with {len(self.pois)} locations")
        except FileNotFoundError:
            print(f"⚠️  POI file not found: {pois_file}")
        except Exception as e:
            print(f"⚠️  Error loading POIs: {e}")

    # UPDATED: Returns 5 items now
    def get_neighbors(self, node_id): return self.adj_list.get(node_id, [])
    def get_node(self, node_id): return self.nodes.get(node_id)
    
    def autocomplete(self, prefix):
        """
        Get autocomplete suggestions for POI search
        Args:
            prefix (str): User's partial input (e.g., "gat")
        Returns:
            list: Matching POI suggestions
        """
        return self.poi_trie.search_prefix(prefix)
    
    # --- THE SMART SNAP ALGORITHM ---
    def find_nearest_node(self, target_lat, target_lon, mode='car'):
        candidates = [] # Store (distance, node_id)
        
        pool = self.drive_nodes if mode == 'car' else self.walk_nodes
        if not pool: pool = self.nodes.keys()

        # 1. Find the top 10 closest nodes mathematically
        for node_id in pool:
            if node_id not in self.nodes: continue
            data = self.nodes[node_id]
            d_lat = data['lat'] - target_lat
            d_lon = data['lon'] - target_lon
            dist_sq = d_lat**2 + d_lon**2
            
            # Optimization: only keep if reasonably close (e.g., within ~200m)
            if dist_sq < 0.00001: 
                candidates.append((dist_sq, node_id))
        
        candidates.sort(key=lambda x: x[0])
        top_candidates = candidates[:5] # Check top 5 closest
        
        if not top_candidates: return None
        
        # 2. Pick the best one based on Topology
        best_node = top_candidates[0][1] # Default to closest
        
        for dist, node_id in top_candidates:
            # Check the edges connected to this node
            neighbors = self.adj_list.get(node_id, [])
            
            # If we are looking for an entrance, prefer 'service' or 'residential'
            # Penalize 'motorway' or 'trunk' (The Highway)
            
            is_highway = False
            is_campus_road = False
            
            for n in neighbors:
                hw_type = n[5] # Index 5 is highway type
                if hw_type in ['motorway', 'trunk', 'primary', 'secondary']:
                    is_highway = True
                if hw_type in ['service', 'residential', 'living_street']:
                    is_campus_road = True
            
            # LOGIC: If the node connects to a campus road, PICK IT immediately.
            # Even if it's 2nd or 3rd closest.
            if is_campus_road:
                return node_id
                
        return best_node