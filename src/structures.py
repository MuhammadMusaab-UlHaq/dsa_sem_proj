import json

# ================= TRIE DATA STRUCTURE (Usman) =================
class TrieNode:
    """Node in the Trie structure for efficient prefix searching."""
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.poi_data = None

class Trie:
    """Trie data structure for autocomplete suggestions."""
    def __init__(self):
        self.root = TrieNode()
        self.all_words = []  # Store all words for fuzzy matching
    
    def insert(self, word, poi_data=None):
        """Insert a word into the Trie."""
        node = self.root
        word_lower = word.lower()
        
        # Store for fuzzy matching
        self.all_words.append({'word': word_lower, 'data': poi_data})
        
        for char in word_lower:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.poi_data = poi_data
    
    def search_prefix(self, prefix):
        """Find all words with given prefix."""
        prefix = prefix.lower()
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                # No exact prefix match - try fuzzy search
                return self._fuzzy_search(prefix)
            node = node.children[char]
        
        suggestions = []
        self._collect_words(node, prefix, suggestions)
        return suggestions[:10]
    
    def _fuzzy_search(self, query, max_distance=2):
        """
        Fuzzy search using Levenshtein distance for typo tolerance.
        Returns words within edit distance of query.
        """
        query = query.lower()
        results = []
        
        for item in self.all_words:
            word = item['word']
            # Check if query is substring
            if query in word:
                results.append({'name': word, 'data': item['data'], 'score': 0})
                continue
            
            # Check edit distance on the beginning of the word
            if len(query) >= 2:
                # Compare query against first N characters of word
                compare_len = min(len(query) + 1, len(word))
                word_prefix = word[:compare_len]
                dist = self._levenshtein(query, word_prefix)
                
                if dist <= max_distance:
                    results.append({'name': word, 'data': item['data'], 'score': dist})
                    continue
                
                # Also check if any word in multi-word names matches
                for sub_word in word.split():
                    if len(sub_word) >= 2:
                        dist = self._levenshtein(query, sub_word[:len(query)+1])
                        if dist <= max_distance:
                            results.append({'name': word, 'data': item['data'], 'score': dist})
                            break
        
        # Sort by score (lower is better match)
        results.sort(key=lambda x: x['score'])
        return results[:10]
    
    def _levenshtein(self, s1, s2):
        """Calculate Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        
        return prev_row[-1]
    
    def _collect_words(self, node, current_word, suggestions):
        """Recursively collect all complete words from current node."""
        if node.is_end_of_word:
            suggestions.append({
                'name': current_word,
                'data': node.poi_data
            })
        
        for char, child_node in node.children.items():
            self._collect_words(child_node, current_word + char, suggestions)

# ================= MERGE SORT (Usman) =================
def merge_sort(data_list, key):
    """
    Recursive Merge Sort implementation from scratch.
    Does NOT use Python's built-in .sort() method.
    
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if len(data_list) <= 1:
        return data_list
    
    mid = len(data_list) // 2
    left_half = data_list[:mid]
    right_half = data_list[mid:]
    
    sorted_left = merge_sort(left_half, key)
    sorted_right = merge_sort(right_half, key)
    
    return _merge(sorted_left, sorted_right, key)

def _merge(left, right, key):
    """Helper function to merge two sorted lists."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result

# ================= MIN HEAP =================
class MinHeap:
    """Priority Queue implementation using Min Heap."""
    def __init__(self):
        self.heap = []
    
    def push(self, item):
        self.heap.append(item)
        self._sift_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap:
            return None
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

# ================= SPATIAL GRID =================
class SpatialGrid:
    """Spatial hash grid for O(1) POI lookup."""
    def __init__(self, cell_size=0.005):
        self.cell_size = cell_size
        self.grid = {}
    
    def add_poi(self, name, lat, lon, type_tag):
        key = (int(lat/self.cell_size), int(lon/self.cell_size))
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append({'name': name, 'lat': lat, 'lon': lon, 'type': type_tag})
    
    def get_nearby(self, lat, lon):
        ck = (int(lat/self.cell_size), int(lon/self.cell_size))
        nearby = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                k = (ck[0]+dx, ck[1]+dy)
                if k in self.grid:
                    nearby.extend(self.grid[k])
        return nearby

# ================= CITY GRAPH =================
class CityGraph:
    """Main graph data structure for the navigation system."""
    def __init__(self):
        self.nodes = {}
        self.adj_list = {}
        self.spatial = SpatialGrid()
        self.drive_nodes = set()
        self.walk_nodes = set()
        self.pois = []
        self.poi_trie = Trie()

    def load_data(self, nodes_file, edges_file, pois_file="pois.json"):
        print("Loading graph data...")
        
        # Load nodes
        with open(nodes_file, 'r') as f:
            nodes_data = json.load(f)
        for n_id, data in nodes_data.items():
            node_id = int(n_id)
            self.nodes[node_id] = {
                'lat': data['lat'],
                'lon': data['lon'],
                'ele': data.get('elevation', 0)
            }
            self.adj_list[node_id] = []

        # Load edges
        with open(edges_file, 'r') as f:
            edges_data = json.load(f)
        for edge in edges_data:
            u, v = int(edge['u']), int(edge['v'])
            if u in self.nodes and v in self.nodes:
                # (v, weight, is_walk, is_drive, geometry, highway_type)
                self.adj_list[u].append((
                    v,
                    edge['weight'],
                    edge['is_walkable'],
                    edge['is_drivable'],
                    edge.get('geometry', ''),
                    edge.get('highway', '')
                ))
                
                if edge['is_drivable']:
                    self.drive_nodes.add(u)
                    self.drive_nodes.add(v)
                if edge['is_walkable']:
                    self.walk_nodes.add(u)
                    self.walk_nodes.add(v)
        
        # ===== MODIFIED: Load POIs from both sources =====
        self.pois = []
        
        # First, try loading custom NUST POIs
        try:
            from nust_pois import get_all_pois
            custom_pois = get_all_pois()
            self.pois.extend(custom_pois)
            print(f"📍 Loaded {len(custom_pois)} custom NUST POIs")
        except ImportError:
            print("⚠️  Custom NUST POIs not found, using OSM data only")
        
        # Then, load from pois.json (OSM data)
        try:
            with open(pois_file, 'r', encoding='utf-8') as f:
                osm_pois = json.load(f)
            
            # Merge, avoiding duplicates by name
            existing_names = {p['name'].lower() for p in self.pois}
            for p in osm_pois:
                if p['name'].lower() not in existing_names:
                    self.pois.append(p)
            
            print(f"📍 Added {len(osm_pois)} OSM POIs (merged total: {len(self.pois)})")
        except FileNotFoundError:
            print(f"⚠️  POI file not found: {pois_file}")
        except Exception as e:
            print(f"⚠️  Error loading OSM POIs: {e}")
        
        # Build spatial index and Trie
        print(f"🔍 Building search index for {len(self.pois)} locations...")
        for p in self.pois:
            self.spatial.add_poi(p['name'], p['lat'], p['lon'], p['type'])
            self.poi_trie.insert(p['name'], p)
        
        print(f"✅ Ready! {len(self.nodes)} nodes, {len(self.pois)} searchable locations")

    def get_neighbors(self, node_id):
        return self.adj_list.get(node_id, [])
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    def autocomplete(self, prefix):
        """Get autocomplete suggestions for POI search."""
        return self.poi_trie.search_prefix(prefix)

    def find_nearest_node(self, target_lat, target_lon, mode='car'):
        """Smart snapping algorithm - prefers campus roads over highways."""
        candidates = []
        
        pool = self.drive_nodes if mode == 'car' else self.walk_nodes
        if not pool:
            pool = self.nodes.keys()

        # Start with tight radius, expand if needed
        # 0.00001 ~= 1m, 0.0001 ~= 10m, 0.001 ~= 100m, 0.01 ~= 1km, 0.1 ~= 10km
        search_radii = [0.00001, 0.0001, 0.001, 0.01, 0.1]
        
        for radius in search_radii:
            candidates = []
            for node_id in pool:
                if node_id not in self.nodes:
                    continue
                data = self.nodes[node_id]
                d_lat = data['lat'] - target_lat
                d_lon = data['lon'] - target_lon
                dist_sq = d_lat**2 + d_lon**2
                
                if dist_sq < radius:
                    candidates.append((dist_sq, node_id))
            
            if candidates:
                break  # Found candidates at this radius
        
        candidates.sort(key=lambda x: x[0])
        top_candidates = candidates[:5]
        
        if not top_candidates:
            return None
        
        best_node = top_candidates[0][1]
        
        for dist, node_id in top_candidates:
            neighbors = self.adj_list.get(node_id, [])
            
            is_campus_road = False
            
            for n in neighbors:
                hw_type = n[5] if len(n) > 5 else ''
                if hw_type in ['service', 'residential', 'living_street']:
                    is_campus_road = True
            
            if is_campus_road:
                return node_id
                
        return best_node