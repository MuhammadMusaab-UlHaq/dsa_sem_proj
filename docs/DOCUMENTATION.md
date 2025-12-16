# NUST Navigation System - Technical Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Structures](#data-structures)
3. [Algorithms](#algorithms)
4. [Modules](#modules)
5. [Data Pipeline](#data-pipeline)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)

---

## System Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         run.py                              │
│                    (Entry Point)                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                      main.py                                │
│            (CLI Interface & Menu System)                    │
│  • Main menu loop          • Route selection                │
│  • User input handling     • Trip time planner              │
│  • Rush hour toggle        • History viewer                 │
└───────┬─────────────┬─────────────┬─────────────┬───────────┘
        │             │             │             │
┌───────▼───────┐ ┌───▼───────┐ ┌───▼───────┐ ┌───▼───────────┐
│ structures.py │ │algorithms │ │visualizer │ │history_manager│
│               │ │    .py    │ │   .py     │ │     .py       │
│ • CityGraph   │ │ • A*      │ │ • HTML    │ │ • Log trips   │
│ • Trie        │ │ • BFS     │ │   maps    │ │ • Get history │
│ • MinHeap     │ │ • K-paths │ │ • Sakura  │ │ • Frequent    │
│ • SpatialGrid │ │ • TSP     │ │   theme   │ │   dests       │
│ • MergeSort   │ │ • Traffic │ │           │ │               │
└───────────────┘ └───────────┘ └───────────┘ └───────────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│                      data/ folder                           │
│  nodes.json (33,874 nodes) │ edges.json (85,251 edges)      │
│  pois.json (830 OSM POIs)  │ + nust_pois.py (175 custom)    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Startup**: `run.py` → `main.py` → `CityGraph.load_data()`
2. **Search**: User query → `Trie.search_prefix()` → Fuzzy match fallback
3. **Routing**: `find_nearest_node()` → Algorithm (A*/BFS/K-paths) → `reconstruct_path()`
4. **Display**: `collect_route_data()` → `display_route_results()` → `generate_map()`

---

## Data Structures

### 1. CityGraph (`structures.py`)

The core graph representation.

```python
class CityGraph:
    nodes: dict[int, {lat, lon, ele}]     # 33,874 nodes
    adj_list: dict[int, list[tuple]]      # Adjacency list
    drive_nodes: set[int]                  # Nodes accessible by car
    walk_nodes: set[int]                   # Nodes accessible on foot
    pois: list[dict]                       # Points of Interest
    poi_trie: Trie                         # For autocomplete
    spatial: SpatialGrid                   # For nearby POI lookup
```

**Edge tuple format:**
```python
(neighbor_id, weight, is_walkable, is_drivable, geometry, highway_type)
```

**Highway types and their speeds:**
| Highway Type | Speed (km/h) | Rush Hour Multiplier |
|--------------|--------------|----------------------|
| motorway     | 90           | 1.5x                 |
| trunk        | 70           | 2.0x                 |
| primary      | 50           | 1.8x                 |
| secondary    | 40           | 1.5x                 |
| tertiary     | 35           | 1.3x                 |
| residential  | 30           | 1.1x                 |
| service      | 20           | 1.0x                 |

### 2. Trie (`structures.py`)

Prefix tree for O(k) autocomplete where k = query length.

```python
class Trie:
    root: TrieNode
    all_words: list  # For fuzzy fallback
    
    def insert(word, poi_data)       # Add POI to trie
    def search_prefix(prefix)        # Get suggestions
    def _fuzzy_search(query, max_distance=2)  # Levenshtein fallback
```

**Fuzzy Search**: Uses Levenshtein distance for typo tolerance. If exact prefix match fails, returns words within edit distance 2.

### 3. MinHeap (`structures.py`)

Custom priority queue for A* (not using `heapq`).

```python
class MinHeap:
    heap: list[tuple]
    
    def push(item)      # O(log n)
    def pop()           # O(log n)
    def is_empty()      # O(1)
```

### 4. SpatialGrid (`structures.py`)

Hash grid for O(1) nearby POI queries.

```python
class SpatialGrid:
    cell_size: 0.005  # ~500m cells
    grid: dict[(i,j), list[POI]]
    
    def add_poi(name, lat, lon, type)
    def get_nearby(lat, lon)  # Returns POIs in 3x3 cell neighborhood
```

### 5. Merge Sort (`structures.py`)

Custom implementation (no `sorted()` or `.sort()`).

```python
def merge_sort(data_list, key) -> list
    # Time: O(n log n)
    # Space: O(n)
    # Used for sorting POIs by distance
```

---

## Algorithms

### 1. A* Search (`algorithms.py`)

Optimal pathfinding with admissible heuristic.

```python
def a_star_search(graph, start_id, end_id, mode='car', return_stats=False):
    # Returns: (path, cost) or (path, cost, stats)
```

**Heuristic**: Straight-line distance / max_speed (admissible - never overestimates)

**Cost Function**:
- **Walking**: Tobler's Hiking Function (accounts for slope)
- **Driving**: `distance / road_speed + intersection_delay`

**Intersection Delay**:
- Normal: 2 sec per 500m on primary/secondary/trunk roads
- Rush hour: 4 sec per 500m

**Stats returned**:
```python
{
    'algorithm_name': 'A* Search',
    'nodes_explored': 14727,
    'heap_operations': 30060,
    'time_ms': 358.0
}
```

### 2. BFS Search (`algorithms.py`)

Finds path with minimum number of edges (fewest turns).

```python
def bfs_search(graph, start, end, return_stats=False):
    # Returns: (path, turn_count) or (path, turn_count, stats)
```

**Use case**: Simple-to-follow directions when time isn't critical.

**Note**: BFS doesn't consider edge weights, so time is calculated post-hoc:
- Walking: `distance / 1.35 m/s` (~5 km/h)
- Driving: `distance / 11.11 m/s` (~40 km/h)

### 3. K-Shortest Paths (`algorithms.py`)

Yen's algorithm variant with edge penalization.

```python
def get_k_shortest_paths(graph, start_id, end_id, k=3, mode='car'):
    # Returns: list[(path, cost)]
```

**How it works**:
1. Find shortest path with A*
2. Penalize edges in that path (10x weight first pass, ∞ subsequent)
3. Repeat k times
4. Restore original edge weights

### 4. TSP Optimization (`algorithms.py`)

Traveling Salesman approximation for multi-stop routes.

```python
def optimize_route_order(graph, start, list_of_stops, mode='car'):
    # Returns: (best_order, total_cost, segment_paths, algo_stats)
```

**Strategy**:
- ≤4 stops: Brute force all permutations
- \>4 stops: Nearest Neighbor heuristic

**Nearest Neighbor**: O(n²) greedy - always pick closest unvisited stop.

### 5. Traffic Simulation (`algorithms.py`)

Flag-based rush hour mode.

```python
RUSH_HOUR_MULTIPLIERS = {
    'trunk': 2.0,      # 100% slower
    'primary': 1.8,    # 80% slower
    'secondary': 1.5,  # 50% slower
    ...
}

def simulate_traffic(graph):
    graph.rush_hour_active = True  # A* reads this flag
```

---

## Modules

### main.py (1246 lines)

**Key Functions**:

| Function | Description |
|----------|-------------|
| `main_menu()` | Main loop with 6 options |
| `route_selection_menu()` | Single route (A*/BFS/K-paths) |
| `multi_stop_route_menu()` | TSP multi-stop optimization |
| `toggle_traffic()` | Rush hour mode control |
| `trip_time_planner()` | Leave-by / Arrive-by calculator |
| `view_history()` | Trip history display |
| `get_user_selection_with_autocomplete()` | POI search with Trie |
| `display_route_results()` | CLI output + map generation |
| `calculate_exact_distance()` | Sum distances along path |

**Time Utilities**:
```python
def is_rush_hour(check_time=None):
    # Morning: 7:00-9:30 AM
    # Evening: 4:30-8:00 PM
    return (is_rush: bool, period: str)

def estimate_travel_delay(graph, start_id, end_id, mode):
    # Returns: (normal_time, rush_time, delay_seconds)
```

### visualizer.py (1629 lines)

Generates sakura-themed HTML maps using Google Maps JavaScript API.

**Features**:
- Route polyline with gradient coloring
- Start/end markers
- POI markers (toggleable by category)
- Elevation profile chart
- Algorithm stats panel
- Multi-stop segment coloring
- Alternative routes (dashed lines)
- Layer controls (Satellite, Terrain, Hybrid)

**POI Categories & Colors**:
```javascript
const categoryColors = {
    'restaurant': '#E57373',
    'cafe': '#8D6E63',
    'fuel': '#FFB74D',
    'parking': '#4FC3F7',
    'hotel': '#9575CD',
    'landmark': '#4DB6AC',
    ...
};
```

### history_manager.py

Simple file-based trip logging.

```python
def log_trip(start_name, end_name, mode, time_min)
def get_history(limit=10) -> list[str]
def get_frequent_destinations(top_n=5) -> list[(dest, count)]
def clear_history()
```

**File format** (`outputs/history.txt`):
```
[2024-12-10 11:43:00] SEECS Car Parking -> F-7 Markaz | Mode: car | Time: 20.4 min
```

### nust_pois.py

POI database for NUST campus and Islamabad.


---

## Data Pipeline

### data_pipeline.py

Downloads and processes map data from OpenStreetMap + Google.

**Configuration**:
```python
LOCATION_POINT = (33.6800, 73.0300)  # Center between NUST and Islamabad
DIST_RADIUS = 8000                    # 8km radius
GOOGLE_API_KEY = "..."                # For elevation data
```

**Process**:
1. Download road network via OSMnx (`network_type='all'`)
2. Fetch elevation for all nodes (Google Elevation API, batched)
3. Extract POIs by tag
4. Save to JSON files

**Edge Classification**:
```python
# Non-drivable roads
['footway', 'steps', 'corridor', 'path', 'cycleway', 'pedestrian', 'track']

# Non-walkable roads
['motorway', 'motorway_link']
```

**Running the pipeline**:
```bash
cd src
python data_pipeline.py
```

⚠️ **Note**: Consumes Google API quota. Run sparingly.

---

## Configuration

### Speed Profiles (algorithms.py)

```python
speed_map = {
    'motorway': 25.0,      # 90 km/h
    'trunk': 19.4,         # 70 km/h
    'primary': 13.9,       # 50 km/h
    'secondary': 11.1,     # 40 km/h
    'tertiary': 9.7,       # 35 km/h
    'residential': 8.3,    # 30 km/h
    'service': 5.6,        # 20 km/h
}
```

### Rush Hour Multipliers (algorithms.py)

```python
RUSH_HOUR_MULTIPLIERS = {
    'motorway': 1.5,
    'trunk': 2.0,
    'primary': 1.8,
    'secondary': 1.5,
    'tertiary': 1.3,
    'residential': 1.1,
}
```

### Walking Speed (algorithms.py)

Uses Tobler's Hiking Function:
```python
speed_kmh = 6 * exp(-3.5 * abs(slope + 0.05))
```
- Flat ground: ~5 km/h
- Uphill: Slower
- Downhill: Faster (up to a point)

---

## API Reference

### CityGraph Methods

```python
# Load data from JSON files
graph.load_data(nodes_file, edges_file, pois_file)

# Get neighbors of a node
graph.get_neighbors(node_id) -> list[tuple]

# Get node data
graph.get_node(node_id) -> {lat, lon, ele}

# Autocomplete search
graph.autocomplete(prefix) -> list[{name, data}]

# Find nearest road node to a coordinate
graph.find_nearest_node(lat, lon, mode='car') -> node_id
```

### Algorithm Functions

```python
# A* pathfinding
a_star_search(graph, start_id, end_id, mode='car', return_stats=False)
    -> (path, cost) | (path, cost, stats)

# BFS (fewest turns)
bfs_search(graph, start, end, return_stats=False)
    -> (path, turns) | (path, turns, stats)

# K alternative routes
get_k_shortest_paths(graph, start_id, end_id, k=3, mode='car')
    -> list[(path, cost)]

# TSP optimization
optimize_route_order(graph, start, stops, mode='car')
    -> (order, cost, segments, stats)

# Traffic control
simulate_traffic(graph)  # Enable rush hour
reset_traffic(graph)     # Disable rush hour
```

### Visualizer Functions

```python
generate_map(
    path_nodes,           # List of node IDs
    all_nodes,            # Node data dict
    route_stats=None,     # {time_sec, distance_m, climb_m, ...}
    algorithm_stats=None, # {nodes_explored, heap_operations, ...}
    pois_along_route=None,
    alternatives=None,    # For K-shortest
    start_name="Start",
    end_name="Destination",
    output_file="map.html",
    multi_stop_segments=None,  # For TSP
    waypoint_labels=None
)
```

---

## Performance Benchmarks

Test route: SEECS Car Parking → F-7 Markaz (~16 km)

| Algorithm | Nodes Explored | Heap Ops | Time |
|-----------|---------------|----------|------|
| A* (driving) | 14,727 | 30,060 | 358 ms |
| A* (walking) | 12,637 | 25,606 | 252 ms |
| BFS | 17,981 | 0 | 22 ms |
| K-Shortest (k=3) | 17,323 | 35,142 | 358 ms |

---

## Team & Contributions

### Muhammad Musaab Ul Haq
- Project architecture & system design
- A* search algorithm with road-type awareness 
- MinHeap priority queue implementation 
- CityGraph & SpatialGrid data structures
- Tobler's Hiking Function for walking speed
- Smart node snapping algorithm 
- Trip time planner - Leave By / Arrive By 
- Custom NUST POIs database 
- Route data collection & integration 
- Branch management & code integration
- Entry point script (`run.py`)
- Final polish & bug fixes

### Usman
- Trie data structure for autocomplete 
- Levenshtein distance for fuzzy/typo-tolerant search 
- Merge Sort implementation from scratch 
- TSP multi-stop optimization 
  - Brute force for ≤4 stops
  - Nearest Neighbor heuristic for >4 stops
- CLI interface & menu system (`main.py`)
- Map visualizer with sakura theme (`visualizer.py`)
- Fun statistics generator 
- POI name formatting & type icons 
- Multi-stop segment visualization 

### Ahmed
- K-Shortest Paths - Yen's algorithm variant 
- Traffic simulation system 
- Rush hour detection logic 
- Traffic impact analysis feature 
- Data pipeline - OSM + Google APIs (`data_pipeline.py`)
- History manager (`history_manager.py`)
- Frequent destinations analysis 
- Report writing & Big-O complexity analysis

### Farida
- BFS search algorithm - fewest turns 
- Navigation stack logic 
- Trip statistics calculation 
- Elevation gain/loss calculation 
- Video production & presentation script

---

## Known Limitations

1. **No real-time traffic** - Rush hour is simulated, not live data
2. **Walking paths incomplete** - OSM doesn't have all campus footpaths
3. **Elevation accuracy** 
4. **No turn-by-turn directions** - Just shows path on map

