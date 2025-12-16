
Since some functionality of the semester project is provided through APIs (for the GUI purpose and elevation data). The API has not been commited to the repo for security reasons.
It is advised to run the project from the zip file, rather than the github repo.
The github repo can be found here: https://github.com/MuhammadMusaab-UlHaq/dsa_sem_proj


# NUST Navigation System

A CLI-based navigation app for NUST campus and Islamabad. Built for our DSA semester project.

**What it does:** Find routes between 1000+ locations using A*, BFS, and TSP algorithms. Walking & driving modes. Rush hour simulation. Interactive HTML maps.

## Quick Start

```bash
pip install -r requirements.txt
python run.py
```

That's it. The app loads 33k+ road nodes and 1000+ POIs on startup.

## Features at a Glance

- **A\* Search** - Fastest route with road-type aware speeds
- **BFS** - Fewest turns (simplest to follow)
- **K-Shortest Paths** - 3 alternative routes
- **TSP Multi-Stop** - Optimal order for visiting multiple places
- **Rush Hour Mode** - Realistic traffic delays on major roads
- **Trip Planner** - "Leave by" / "Arrive by" time calculations
- **Fuzzy Search** - Typo-tolerant POI search using Levenshtein distance

## Data Sources

- Road network: OpenStreetMap (8km radius from NUST)
- Elevation: Google Maps Elevation API
- POIs: OSM + 175 hand-curated NUST locations

## The Stack

```
Python 3.10+
├── OSMnx (road data)
├── NetworkX (graph ops)
└── Google Maps API (elevation + map tiles)
```

## Project Structure

```
src/
├── main.py         # CLI, menus, user interaction
├── algorithms.py   # A*, BFS, K-shortest, TSP
├── structures.py   # Graph, Trie, MinHeap, Merge Sort
├── visualizer.py   # HTML map generator (sakura theme)
├── history_manager.py
├── nust_pois.py    # Hand-curated NUST POIs
└── data_pipeline.py # Downloads fresh data from OSM/Google
```

## Team

- **Muhammad Musaab Ul Haq** - Project architecture, A* algorithm, trip planner, integration & polish.
- **Usman** - Trie autocomplete, Merge Sort, TSP optimization, UI/CLI design.
- **Ahmed** - K-shortest paths, Traffic simulation, report submission, analysis of all data structures, big-oh table creation.
- **Farida** - BFS search, Navigation stack, Trip stats calculation, video making, script making for the submission of the project.

## Notes

- First run takes ~5 sec to load the graph
- Maps open automatically in browser after route calculation
- Rush hour = 7-9:30 AM and 4:30-8 PM
- Travel times are calibrated for Islamabad traffic (~40 km/h urban average)

## Sample Output

```
 Algorithm: A* Search
 Nodes Explored: 14,727
 Heap Operations: 30,060
  Compute Time: 358 ms

==============================
   TRIP STATISTICS (CAR)
==============================
Est. Time      : 20.4 min
Total Distance : 15872 meters
Est. Fuel Cost : PKR 2380.74
==============================
```

---

For detailed documentation, see [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md)
