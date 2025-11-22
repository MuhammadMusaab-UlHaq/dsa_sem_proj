# NUST Navigation System - Quick Reference Guide

## 🚀 Quick Commands

### First Time Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Download map data
python data_pipeline.py
```

### Regular Use
```powershell
# Launch application (if data exists)
python main.py

# Rebuild data from scratch
.\scripts\cleanup_data.ps1
python data_pipeline.py
```

---

## 📋 Demo Script (For Dr. Ayesha)

### Setup (Before Demo)
1. Ensure internet connection is active
2. Run: `python data_pipeline.py`
3. Wait for "Done." message

### Feature Demonstrations

#### 1️⃣ Core Pathfinding (A* Algorithm)
**Input:**
- Start: `Concordia 1`
- End: `NUST Gate 2`
- Mode: `Driving`

**Show:** Blue route line on map

**Say:** *"Our A* implementation uses real OpenStreetMap data with Euclidean heuristic for optimal pathfinding."*

---

#### 2️⃣ Topology Awareness (Tobler's Function)
**Input:**
- Same route as above
- Mode: `Walking`

**Show:** Different estimated time in console

**Say:** *"Walking mode applies Tobler's Hiking Function, which penalizes uphill slopes. Notice the time difference compared to driving."*

---

#### 3️⃣ Smart Snapping (Topology Analysis)
**Input:**
- Start: `Gate 2`
- End: Any location

**Show:** Route starts inside campus, not on highway

**Say:** *"Standard GIS systems snap to the nearest point - often the highway. Our smart snapping algorithm analyzes road topology to prefer campus entrances."*

---

#### 4️⃣ POI Discovery (Spatial Hash Grid)
**Input:**
- Any route calculation

**Show:** Console output listing nearby POIs

**Say:** *"We use a spatial hash grid for O(1) POI lookup. The system finds amenities within 50 meters of your route without scanning the entire database."*

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No POIs loaded" | Run `python data_pipeline.py` |
| "No path found" | Verify locations are within campus |
| Pipeline timeout | Wait and retry - multiple servers available |
| Old data warnings | Run `.\scripts\cleanup_data.ps1` |

---

## 📊 Key Metrics to Highlight

- **Graph Size:** ~800 nodes, ~2000 edges (NUST campus)
- **A* Complexity:** O((V + E) log V)
- **POI Lookup:** O(1) average case
- **Data Source:** Real OpenStreetMap data
- **Elevation Data:** Open-Elevation API

---

## 🎯 Validation Checklist

- [ ] `nodes.json` exists and > 50 KB
- [ ] `edges.json` exists and > 100 KB
- [ ] `pois.json` exists and contains gates
- [ ] Test driving route works
- [ ] Test walking route shows different time
- [ ] Gate snapping works correctly
- [ ] Map opens in browser automatically

---

## 📞 Emergency Commands

```powershell
# Complete reset
.\scripts\cleanup_data.ps1
python data_pipeline.py

# Test everything
python tests\test_structures.py
python tests\test_algorithms.py
```

---

**Last Updated:** November 2025  
**Status:** ✅ MVP Deployment Ready
