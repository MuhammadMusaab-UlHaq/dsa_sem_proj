# NUST Intelligent Navigation System
**MVP Deployment Ready** ✓

An intelligent pathfinding system for NUST campus using real OpenStreetMap data, custom A* algorithm with topographic awareness, and smart geospatial snapping.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Internet connection (for data download)

### Installation
```powershell
# Install dependencies
pip install -r requirements.txt
```

### Launch
```powershell
# First time: Download and process map data
python data_pipeline.py

# Then run the application
python main.py
```

---

## 📋 Launch Checklist

### 1. Environment Setup
The `requirements.txt` includes all necessary dependencies:
- `osmnx>=1.9.0` - OpenStreetMap data processing
- `requests` - API calls
- `shapely` - Geometry operations
- `networkx` - Graph data structures
- `scikit-learn` - Spatial indexing

**Action:** Run `pip install -r requirements.txt`

### 2. Execution Order (Critical)

**⚠️ IMPORTANT:** You must rebuild the database because the data structure now includes `highway` tags for smart snapping.

1. **Delete old data** (automated):
   ```powershell
   .\scripts\cleanup_data.ps1
   ```
   This removes: `nodes.json`, `edges.json`, `pois.json`, `nust_raw.osm`, `map.html`

2. **Run Pipeline**:
   ```powershell
   python data_pipeline.py
   ```
   - Downloads fresh data from OpenStreetMap
   - Processes road network topology
   - Extracts POIs (Gates, Buildings, Amenities)
   - Watch for: `[5/5] Saving Database...`

3. **Run Application**:
   ```powershell
   python main.py
   ```

### 3. Demo Script (For Presentation)

Follow this sequence to demonstrate all 4 MVP features:

#### **Feature 1: Core Pathfinding (A* Algorithm)**
- **Action:** 
  - Start: `Concordia 1`
  - End: `NUST Gate 2`
  - Mode: `Driving`
- **Expected Result:** Blue line showing route along roads
- **Talking Point:** *"We use A* with Euclidean heuristic. The graph is built from real OpenStreetMap data parsed via Python."*

#### **Feature 2: Topology Awareness (Elevation/Slope)**
- **Action:** Run the same route with Mode: `Walking`
- **Expected Result:** Different estimated time
- **Talking Point:** *"Notice the time difference. Our algorithm applies Tobler's Hiking Function to penalize uphill movement for pedestrians, whereas cars use standard speed limits."*

#### **Feature 3: Smart Snapping (The "Gate" Check)**
- **Action:** Search for `Gate 2` specifically
- **Expected Result:** Path starts inside campus, NOT on the highway
- **Talking Point:** *"A standard GIS would snap to the highway because it's mathematically closer. Our system analyzes edge topology (Service Road vs. Highway) to intelligently snap to the correct campus entrance."*

#### **Feature 4: POI Search (Spatial Hashing)**
- **Action:** Look at console output after route calculation
- **Expected Result:** Lists nearby locations (e.g., "Electrobes", "Hostels")
- **Talking Point:** *"Instead of scanning the whole database (O(N)), we use a Spatial Hash Grid (O(1)) to instantly find amenities within 50 meters of the calculated path."*

---

## 🏗️ Project Structure

```
dsa_sem_proj/
├── algorithms.py          # A* pathfinding, Tobler's function
├── structures.py          # MinHeap, SpatialGrid, CityGraph
├── data_pipeline.py       # OSM data download & processing
├── visualizer.py          # MapLibre GL JS map generation
├── main.py                # User interface & application logic
├── requirements.txt       # Python dependencies
│
├── data/                  # (Generated data files)
│   ├── nodes.json         # Graph nodes with elevation
│   ├── edges.json         # Graph edges with highway tags
│   └── pois.json          # Points of Interest
│
├── tests/                 
│   ├── test_structures.py # Data structure validation
│   └── test_algorithms.py # Pathfinding validation
│
├── scripts/
│   └── cleanup_data.ps1   # Clean old data files
│
└── docs/
    └── README.md          # This file
```

---

## 🔧 Technical Features

### Smart Snapping Algorithm
The system doesn't just find the closest node - it analyzes road topology:
```python
# Prefers campus roads over highways
if hw_type in ['service', 'residential', 'living_street']:
    return node_id  # Campus entrance!
```

### Topology-Aware Pathfinding
- **Walking Mode:** Uses Tobler's Hiking Function to penalize slopes
- **Driving Mode:** Adjusts speed based on elevation change
- **Heuristic:** Euclidean distance with mode-specific max speeds

### Data Structure (6-tuple)
Each edge stores: `(neighbor_id, weight, is_walkable, is_drivable, geometry, highway_type)`

### Spatial Hash Grid
O(1) POI lookup using geographic grid cells (0.005° resolution ≈ 550m)

---

## 🧪 Testing

### Run All Tests
```powershell
python tests\test_structures.py  # Validates graph loading, heap, spatial grid
python tests\test_algorithms.py  # Validates A*, multi-stop routing
```

---

## 📊 Key Algorithms

### A* Pathfinding
- **Time Complexity:** O((V + E) log V)
- **Space Complexity:** O(V)
- **Heuristic:** Euclidean distance / max_speed

### Tobler's Hiking Function
```
speed = 6 * exp(-3.5 * |slope + 0.05|) km/h
```

### Spatial Hash Grid
- **Insertion:** O(1)
- **Query:** O(1) average case
- **Cell Size:** 0.005° (≈550m)

---

## 🎯 Demo Validation Checklist

Before presenting:
- [ ] Clean old data: `.\scripts\cleanup_data.ps1` (if needed)
- [ ] Run `python data_pipeline.py` (wait for "Done.")
- [ ] Verify `nodes.json`, `edges.json`, `pois.json` exist
- [ ] Test Feature 1: Basic pathfinding (Driving)
- [ ] Test Feature 2: Walking mode (different time)
- [ ] Test Feature 3: Gate snapping (inside campus)
- [ ] Test Feature 4: POI listing in console
- [ ] Verify `map.html` opens in browser

---

## 🐛 Troubleshooting

### "No POIs loaded" Error
**Cause:** `pois.json` missing  
**Fix:** Run `python data_pipeline.py`

### "No path found"
**Cause:** Start/end in different graph components  
**Fix:** Ensure locations are within NUST campus radius (2km from center)

### Pipeline Timeout
**Cause:** Slow internet or Overpass API congestion  
**Fix:** Script tries multiple servers automatically. Wait for "[1/5] Downloading..."

### Wrong Snapping Location
**Cause:** Old data without `highway` tags  
**Fix:** Delete old data files and re-run pipeline

---

## 📚 Data Sources

- **Map Data:** OpenStreetMap (Overpass API)
- **Elevation:** Open-Elevation API
- **Tiles:** OpenFreeMap (MapLibre GL JS)

---

## 🎓 Academic Context

**Course:** Data Structures & Algorithms (DSA)  
**Institution:** NUST  
**Key Concepts:**
- Graph Theory (Adjacency List)
- Priority Queue (MinHeap)
- Spatial Data Structures (Hash Grid)
- Heuristic Search (A*)
- Computational Geometry

---

## 📝 License

Academic Project - NUST 2025

---

## 🏁 Final Pre-Demo Command

```powershell
# Run tests
python tests\test_structures.py
python tests\test_algorithms.py

# Then launch the app
python main.py
```

**Status:** ✅ **APPROVED FOR MVP DEPLOYMENT**

---

*Generated for NUST DSA Semester Project - November 2025*
