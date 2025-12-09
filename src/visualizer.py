# src/visualizer.py
"""
Sakura-themed Route Visualizer - v2 (All Layout Issues Fixed)
"""

import webbrowser
import os
import json
from datetime import datetime

# Google Maps API Key - set via environment variable
GOOGLE_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

def generate_map(
    path_nodes,
    all_nodes,
    route_stats=None,
    algorithm_stats=None,
    pois_along_route=None,
    alternatives=None,
    start_name="Start",
    end_name="Destination",
    output_file="map.html",
    multi_stop_segments=None,
    waypoint_labels=None
):
    """Generates a Sakura-themed map visualization with fixed layout."""
    
    if os.path.dirname(output_file) == "":
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "outputs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, output_file)

    if not path_nodes or len(path_nodes) < 2:
        print("Error: Not enough nodes to plot a path.")
        return

    def get_node(nid):
        return all_nodes.get(str(nid)) or all_nodes.get(int(nid))

    route_coords = []
    elevations = []
    for node_id in path_nodes:
        n = get_node(node_id)
        if n:
            route_coords.append({"lat": n['lat'], "lng": n['lon']})
            elevations.append(n.get('ele', n.get('elevation', 0)))

    start_node = get_node(path_nodes[0])
    end_node = get_node(path_nodes[-1])

    if not start_node or not end_node:
        print("Error: Could not find start/end node coordinates.")
        return

    if route_stats is None:
        route_stats = {
            'time_sec': 0, 'distance_m': 0, 'climb_m': 0, 'descent_m': 0,
            'mode': 'walk', 'calories': 0, 'fuel_cost': 0
        }
    
    if algorithm_stats is None:
        algorithm_stats = {
            'nodes_explored': 0, 'heap_operations': 0, 'time_ms': 0, 'algorithm_name': 'A*'
        }
    
    if pois_along_route is None:
        pois_along_route = []

    alt_routes_js = "[]"
    if alternatives and len(alternatives) > 1:
        alt_data = []
        for i, (alt_path, alt_cost) in enumerate(alternatives[1:], 2):
            alt_coords = []
            for nid in alt_path:
                n = get_node(nid)
                if n:
                    alt_coords.append({"lat": n['lat'], "lng": n['lon']})
            alt_data.append({
                "coords": alt_coords,
                "time_min": round(alt_cost / 60, 1),
                "label": f"Route {i}"
            })
        alt_routes_js = json.dumps(alt_data)

    # Handle multi-stop segments
    multi_stop_js = "[]"
    waypoints_js = "[]"
    if multi_stop_segments and len(multi_stop_segments) > 0:
        segments_data = []
        for seg_path in multi_stop_segments:
            seg_coords = []
            for nid in seg_path:
                n = get_node(nid)
                if n:
                    seg_coords.append({"lat": n['lat'], "lng": n['lon']})
            segments_data.append(seg_coords)
        multi_stop_js = json.dumps(segments_data)
        
        # Create waypoint markers
        if waypoint_labels:
            waypoints_data = []
            for i, label in enumerate(waypoint_labels):
                if i == 0:
                    # Start point
                    coord = route_coords[0] if route_coords else None
                elif i <= len(multi_stop_segments):
                    # Get last point of segment i-1
                    seg = multi_stop_segments[i-1]
                    n = get_node(seg[-1])
                    coord = {"lat": n['lat'], "lng": n['lon']} if n else None
                else:
                    coord = None
                    
                if coord:
                    waypoints_data.append({"label": label, "coord": coord, "order": i})
            waypoints_js = json.dumps(waypoints_data)

    # Serialize POIs to JS for map markers
    pois_js = json.dumps([
        {"name": p.get('name', 'Unknown'), "lat": p.get('lat'), "lng": p.get('lon'), "type": p.get('type', 'poi'), "distance_m": p.get('distance_m', 0)}
        for p in pois_along_route if p.get('lat') and p.get('lon')
    ])

    fun_stats = generate_fun_stats(route_stats)
    
    html_content = build_html(
        route_coords=route_coords,
        elevations=elevations,
        start_name=start_name,
        end_name=end_name,
        start_coord={"lat": start_node['lat'], "lng": start_node['lon']},
        end_coord={"lat": end_node['lat'], "lng": end_node['lon']},
        route_stats=route_stats,
        algorithm_stats=algorithm_stats,
        pois=pois_along_route,
        alternatives_js=alt_routes_js,
        fun_stats=fun_stats,
        multi_stop_js=multi_stop_js,
        waypoints_js=waypoints_js,
        pois_js=pois_js
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"🗺️  Map Generated: {output_file}")
    try:
        webbrowser.open('file://' + os.path.realpath(output_file))
    except:
        pass


def generate_fun_stats(route_stats):
    """Generate fun, relatable statistics."""
    distance_m = route_stats.get('distance_m', 0)
    time_sec = route_stats.get('time_sec', 0)
    climb_m = route_stats.get('climb_m', 0)
    mode = route_stats.get('mode', 'walk')
    
    fun = []
    
    if distance_m > 0:
        football_fields = distance_m / 100
        if football_fields >= 1:
            fun.append(f"🏈 Distance equals {football_fields:.1f} football fields")
        
        if distance_m >= 100:
            blue_whales = distance_m / 30
            fun.append(f"🐋 That's {blue_whales:.0f} blue whales lined up")
    
    if climb_m > 0:
        floors = climb_m / 3
        if floors >= 1:
            fun.append(f"🏢 You'll climb {floors:.0f} floors of elevation")
        
        if climb_m >= 8:
            giraffes = climb_m / 5.5
            fun.append(f"🦒 Elevation = {giraffes:.1f} giraffes tall")
    
    if mode == 'walk':
        calories = route_stats.get('calories', (distance_m / 1000) * 50)
        if calories > 0:
            samosas = calories / 150
            if samosas >= 0.5:
                fun.append(f"🥟 Burns {samosas:.1f} samosas worth of energy")
    
    if time_sec > 0:
        songs = time_sec / 210
        if songs >= 1:
            fun.append(f"🎵 About {songs:.0f} songs on your playlist")
    
    return fun[:3]  # Return top 3 only to save space


def build_html(route_coords, elevations, start_name, end_name, start_coord, end_coord,
               route_stats, algorithm_stats, pois, alternatives_js, fun_stats,
               multi_stop_js="[]", waypoints_js="[]", pois_js="[]"):
    """Build the complete HTML document with fixed layout."""
    
    time_min = route_stats.get('time_sec', 0) / 60
    distance_km = route_stats.get('distance_m', 0) / 1000
    climb = route_stats.get('climb_m', 0)
    descent = route_stats.get('descent_m', 0)
    mode = route_stats.get('mode', 'walk')
    mode_display = "Walking" if mode == 'walk' else "Driving"
    mode_icon = "directions_walk" if mode == 'walk' else "directions_car"
    
    # Check if this is a multi-stop route
    is_multi_stop = multi_stop_js != "[]"
    
    if mode == 'walk':
        energy_label = "Calories"
        energy_value = f"{route_stats.get('calories', 0):.0f} kcal"
    else:
        energy_label = "Fuel Cost"
        energy_value = f"PKR {route_stats.get('fuel_cost', 0):.0f}"
    
    algo_name = algorithm_stats.get('algorithm_name', 'A*')
    nodes_explored = algorithm_stats.get('nodes_explored', 0)
    heap_ops = algorithm_stats.get('heap_operations', 0)
    compute_time = algorithm_stats.get('time_ms', 0)
    
    # Additional TSP stats
    a_star_calls = algorithm_stats.get('a_star_calls', 0)
    permutations_checked = algorithm_stats.get('permutations_checked', 0)
    
    pois_html = ""
    if pois:
        for p in pois[:4]:  # Limit to 4 to save space
            pois_html += f'''
                <div class="poi-item">
                    <span class="poi-name">{p.get('name', 'Unknown')}</span>
                    <span class="poi-distance">{p.get('distance_m', 0):.0f}m</span>
                </div>'''
    else:
        pois_html = '<div class="poi-item"><span class="poi-name" style="opacity:0.6">No POIs found nearby</span></div>'
    
    fun_stats_html = ""
    for stat in fun_stats:
        fun_stats_html += f'<div class="fun-stat">{stat}</div>'
    if not fun_stats:
        fun_stats_html = '<div class="fun-stat">🎯 You\'re on your way!</div>'
    
    elevation_json = json.dumps(elevations)
    route_coords_json = json.dumps(route_coords)
    current_time = datetime.now().strftime("%B %d, %Y • %I:%M %p")

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{end_name} | NUST Navigator</title>
    <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Noto+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
    <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_API_KEY}"></script>
    <style>
        :root {{
            --sakura-50: #FFF5F7;
            --sakura-100: #FFEEF2;
            --sakura-200: #FFD6E0;
            --sakura-300: #FFB7C5;
            --sakura-400: #FF8FA3;
            --sakura-500: #E75480;
            --sakura-600: #C44569;
            --brown-800: #5D3A4B;
            --brown-900: #3D2533;
            --cream: #FFFBFC;
            --shadow-soft: 0 4px 20px rgba(93, 58, 75, 0.12);
            --shadow-medium: 0 8px 30px rgba(93, 58, 75, 0.18);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Noto Sans', sans-serif;
            background: var(--sakura-50);
            color: var(--brown-800);
            overflow: hidden;
        }}

        /* ========== CHERRY BLOSSOM PETALS ========== */
        .petal {{
            position: fixed;
            width: 10px;
            height: 10px;
            background: var(--sakura-300);
            border-radius: 150% 0 150% 0;
            opacity: 0;
            pointer-events: none;
            z-index: 9999;
            animation: fall linear infinite;
        }}
        .petal:nth-child(odd) {{ background: var(--sakura-200); }}
        .petal:nth-child(3n) {{ background: var(--sakura-400); width: 8px; height: 8px; }}

        @keyframes fall {{
            0% {{ opacity: 0; transform: translateX(0) translateY(-10vh) rotate(0deg); }}
            10% {{ opacity: 0.9; }}
            90% {{ opacity: 0.9; }}
            100% {{ opacity: 0; transform: translateX(80px) translateY(105vh) rotate(540deg); }}
        }}

        /* ========== START PAGE ========== */
        .start-page {{
            position: fixed;
            inset: 0;
            background: linear-gradient(135deg, var(--sakura-100) 0%, var(--sakura-50) 50%, var(--cream) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            transition: opacity 0.5s ease, transform 0.5s ease;
        }}
        .start-page.hidden {{
            opacity: 0;
            transform: scale(1.02);
            pointer-events: none;
        }}

        .start-card {{
            background: white;
            border-radius: 20px;
            padding: 40px 44px;
            max-width: 480px;
            width: 90%;
            box-shadow: var(--shadow-medium);
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .start-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 5px;
            background: linear-gradient(90deg, var(--sakura-300), var(--sakura-500), var(--sakura-300));
        }}

        .brand {{
            font-family: 'Quicksand', sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: var(--sakura-500);
            text-transform: uppercase;
            letter-spacing: 2.5px;
            margin-bottom: 6px;
        }}
        .start-title {{
            font-family: 'Quicksand', sans-serif;
            font-size: 24px;
            font-weight: 700;
            color: var(--brown-900);
            margin-bottom: 28px;
        }}

        .route-visual {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            margin-bottom: 28px;
            padding: 20px;
            background: var(--sakura-50);
            border-radius: 14px;
        }}
        .location-badge {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
        }}
        .location-dot {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 16px;
        }}
        .location-dot.start {{ background: linear-gradient(135deg, #10B981, #059669); }}
        .location-dot.end {{ background: linear-gradient(135deg, var(--sakura-500), var(--sakura-600)); }}
        .location-name {{
            font-size: 12px;
            font-weight: 500;
            color: var(--brown-800);
            max-width: 100px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .route-line {{
            flex: 1;
            height: 3px;
            background: linear-gradient(90deg, #10B981, var(--sakura-500));
            border-radius: 2px;
            position: relative;
            max-width: 100px;
        }}
        .route-line::after {{
            content: '';
            position: absolute;
            right: -5px;
            top: 50%;
            transform: translateY(-50%);
            border: 5px solid transparent;
            border-left-color: var(--sakura-500);
        }}

        .quick-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .quick-stat {{
            padding: 14px 8px;
            background: var(--sakura-50);
            border-radius: 10px;
        }}
        .quick-stat-value {{
            font-family: 'Quicksand', sans-serif;
            font-size: 22px;
            font-weight: 700;
            color: var(--brown-900);
        }}
        .quick-stat-label {{
            font-size: 11px;
            color: var(--brown-800);
            opacity: 0.7;
            margin-top: 2px;
        }}

        .mode-badge {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 14px;
            background: var(--sakura-100);
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
            color: var(--sakura-600);
            margin-bottom: 20px;
        }}
        .mode-badge .material-icons-round {{ font-size: 16px; }}

        .explore-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 14px 36px;
            background: linear-gradient(135deg, var(--sakura-500), var(--sakura-600));
            color: white;
            border: none;
            border-radius: 50px;
            font-family: 'Quicksand', sans-serif;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 15px rgba(231, 84, 128, 0.3);
        }}
        .explore-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(231, 84, 128, 0.4);
        }}
        .explore-btn .material-icons-round {{ font-size: 18px; }}

        .generated-time {{
            font-size: 10px;
            color: var(--brown-800);
            opacity: 0.4;
            margin-top: 20px;
        }}

        /* ========== MAP VIEW ========== */
        .map-view {{
            position: fixed;
            inset: 0;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s ease;
        }}
        .map-view.active {{
            opacity: 1;
            pointer-events: auto;
        }}
        #map {{ width: 100%; height: 100%; }}

        /* ========== FIXED: Panel Container with proper spacing ========== */
        .panel-container {{
            position: fixed;
            top: 24px;           /* FIXED: More top padding */
            right: 20px;
            bottom: 50px;        /* FIXED: Space for Google attribution */
            width: 300px;        /* FIXED: Slightly narrower */
            display: flex;
            flex-direction: column;
            gap: 10px;
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 6px;
            padding-bottom: 10px;
            z-index: 100;
        }}
        
        /* FIXED: Visible scrollbar styling */
        .panel-container::-webkit-scrollbar {{
            width: 5px;
        }}
        .panel-container::-webkit-scrollbar-track {{
            background: rgba(255,255,255,0.3);
            border-radius: 3px;
        }}
        .panel-container::-webkit-scrollbar-thumb {{
            background: var(--sakura-400);
            border-radius: 3px;
        }}
        .panel-container::-webkit-scrollbar-thumb:hover {{
            background: var(--sakura-500);
        }}

        /* Scroll fade indicator at bottom */
        .panel-container::after {{
            content: '';
            position: sticky;
            bottom: 0;
            left: 0;
            right: 0;
            height: 20px;
            background: linear-gradient(transparent, rgba(255,255,255,0.8));
            pointer-events: none;
            flex-shrink: 0;
        }}

        .panel {{
            background: white;
            border-radius: 14px;
            box-shadow: var(--shadow-soft);
            overflow: hidden;
            flex-shrink: 0;
        }}

        .panel-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 14px;
            background: var(--sakura-50);
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }}
        .panel-header:hover {{ background: var(--sakura-100); }}
        
        .panel-title {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: 'Quicksand', sans-serif;
            font-weight: 600;
            font-size: 13px;
            color: var(--brown-900);
        }}
        .panel-title .material-icons-round {{
            font-size: 18px;
            color: var(--sakura-500);
        }}
        .panel-toggle {{
            color: var(--brown-800);
            opacity: 0.5;
            transition: transform 0.3s;
            font-size: 20px;
        }}
        .panel.collapsed .panel-toggle {{ transform: rotate(-90deg); }}

        .panel-content {{
            padding: 14px;
            display: grid;
            gap: 10px;
            max-height: 300px;
            overflow: hidden;
            transition: max-height 0.3s ease, padding 0.3s ease, opacity 0.3s ease;
        }}
        .panel.collapsed .panel-content {{
            max-height: 0;
            padding-top: 0;
            padding-bottom: 0;
            opacity: 0;
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .stat-item {{
            padding: 10px;
            background: var(--sakura-50);
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-family: 'Quicksand', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: var(--brown-900);
        }}
        .stat-label {{
            font-size: 10px;
            color: var(--brown-800);
            opacity: 0.7;
            margin-top: 2px;
        }}

        /* Algorithm Card */
        .algo-card {{
            padding: 12px;
            background: linear-gradient(135deg, var(--sakura-100), var(--sakura-50));
            border-radius: 8px;
            border-left: 3px solid var(--sakura-500);
        }}
        .algo-name {{
            font-family: 'Quicksand', sans-serif;
            font-weight: 700;
            font-size: 14px;
            color: var(--brown-900);
            margin-bottom: 6px;
        }}
        .algo-stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .algo-stat {{
            font-size: 11px;
            color: var(--brown-800);
        }}
        .algo-stat strong {{ color: var(--sakura-600); }}

        /* POI List */
        .poi-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 10px;
            background: var(--sakura-50);
            border-radius: 6px;
        }}
        .poi-name {{
            font-size: 12px;
            font-weight: 500;
            color: var(--brown-800);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 180px;
        }}
        .poi-distance {{
            font-size: 11px;
            font-weight: 600;
            color: var(--sakura-600);
            flex-shrink: 0;
        }}

        /* Fun Stats */
        .fun-stat {{
            padding: 8px 12px;
            background: linear-gradient(135deg, #FEF3C7, #FDE68A);
            border-radius: 6px;
            font-size: 12px;
            color: #92400E;
            border-left: 3px solid #F59E0B;
        }}

        /* FIXED: Elevation Chart with proper padding */
        .elevation-chart {{
            height: 70px;
            background: var(--sakura-50);
            border-radius: 8px;
            padding: 12px 10px 8px 10px;  /* FIXED: More padding */
            position: relative;
        }}
        .elevation-svg {{
            width: 100%;
            height: 100%;
            overflow: visible;
        }}
        .elevation-path {{
            fill: none;
            stroke: var(--sakura-500);
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}
        .elevation-fill {{
            fill: url(#elevationGradient);
            opacity: 0.4;
        }}
        .elevation-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: var(--brown-800);
            opacity: 0.5;
            margin-top: 4px;
        }}

        /* FIXED: Control buttons group on left side */
        .left-controls {{
            position: fixed;
            top: 24px;
            left: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 100;
        }}

        .control-btn {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            background: white;
            border: none;
            border-radius: 50px;
            font-family: 'Quicksand', sans-serif;
            font-size: 13px;
            font-weight: 600;
            color: var(--brown-800);
            cursor: pointer;
            box-shadow: var(--shadow-soft);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .control-btn:hover {{
            transform: translateY(-1px);
            box-shadow: var(--shadow-medium);
        }}
        .control-btn .material-icons-round {{ font-size: 18px; }}
        
        .control-btn.active {{
            background: var(--sakura-500);
            color: white;
        }}

        /* Map Type Selector Group */
        .map-type-group {{
            display: flex;
            background: white;
            border-radius: 12px;
            padding: 4px;
            box-shadow: var(--shadow-soft);
            gap: 2px;
        }}
        .map-type-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            color: var(--brown-800);
            transition: all 0.2s;
        }}
        .map-type-btn:hover {{
            background: var(--sakura-100);
        }}
        .map-type-btn.active {{
            background: var(--sakura-500);
            color: white;
        }}
        .map-type-btn .material-icons-round {{
            font-size: 20px;
        }}

        /* POI Filter Popup */
        .poi-filter-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(139, 69, 79, 0.3);
            backdrop-filter: blur(4px);
            z-index: 500;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }}
        .poi-filter-overlay.active {{
            opacity: 1;
            visibility: visible;
        }}
        
        .poi-filter-popup {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0.9);
            background: linear-gradient(135deg, #FFF5F7 0%, #FFFFFF 100%);
            border-radius: 24px;
            padding: 0;
            width: 360px;
            max-height: 70vh;
            box-shadow: 0 25px 50px -12px rgba(139, 69, 79, 0.25);
            z-index: 501;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            overflow: hidden;
        }}
        .poi-filter-popup.active {{
            opacity: 1;
            visibility: visible;
            transform: translate(-50%, -50%) scale(1);
        }}
        
        .poi-popup-header {{
            background: linear-gradient(135deg, var(--sakura-500) 0%, var(--sakura-600) 100%);
            padding: 20px 24px;
            position: relative;
            overflow: hidden;
        }}
        .poi-popup-header::before {{
            content: '🌸';
            position: absolute;
            top: -10px;
            right: 20px;
            font-size: 60px;
            opacity: 0.2;
        }}
        .poi-popup-header h3 {{
            margin: 0;
            font-family: 'Quicksand', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: white;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .poi-popup-header p {{
            margin: 6px 0 0 0;
            font-size: 12px;
            color: rgba(255,255,255,0.8);
        }}
        .poi-popup-close {{
            position: absolute;
            top: 16px;
            right: 16px;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: none;
            background: rgba(255,255,255,0.2);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .poi-popup-close:hover {{
            background: rgba(255,255,255,0.3);
            transform: rotate(90deg);
        }}
        
        .poi-popup-actions {{
            display: flex;
            gap: 8px;
            padding: 16px 20px;
            background: var(--sakura-50);
            border-bottom: 1px solid var(--sakura-100);
        }}
        .poi-action-btn {{
            flex: 1;
            padding: 10px 16px;
            border: 2px solid var(--sakura-300);
            border-radius: 12px;
            background: white;
            font-family: 'Quicksand', sans-serif;
            font-size: 12px;
            font-weight: 600;
            color: var(--sakura-600);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }}
        .poi-action-btn:hover {{
            background: var(--sakura-500);
            border-color: var(--sakura-500);
            color: white;
        }}
        .poi-action-btn .material-icons-round {{
            font-size: 16px;
        }}
        
        .poi-popup-list {{
            padding: 12px 16px;
            max-height: 320px;
            overflow-y: auto;
        }}
        .poi-popup-list::-webkit-scrollbar {{
            width: 6px;
        }}
        .poi-popup-list::-webkit-scrollbar-track {{
            background: var(--sakura-50);
            border-radius: 3px;
        }}
        .poi-popup-list::-webkit-scrollbar-thumb {{
            background: var(--sakura-300);
            border-radius: 3px;
        }}
        
        .poi-category-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            margin-bottom: 6px;
            background: white;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }}
        .poi-category-item:hover {{
            background: var(--sakura-50);
            transform: translateX(4px);
        }}
        .poi-category-item.selected {{
            border-color: var(--sakura-400);
            background: linear-gradient(135deg, var(--sakura-50) 0%, white 100%);
        }}
        
        .poi-category-icon {{
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
        }}
        .poi-category-info {{
            flex: 1;
        }}
        .poi-category-name {{
            font-family: 'Quicksand', sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: var(--brown-900);
            text-transform: capitalize;
        }}
        .poi-category-count {{
            font-size: 11px;
            color: var(--brown-800);
            opacity: 0.6;
        }}
        .poi-category-check {{
            width: 24px;
            height: 24px;
            border-radius: 8px;
            border: 2px solid var(--sakura-300);
            background: white;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}
        .poi-category-item.selected .poi-category-check {{
            background: var(--sakura-500);
            border-color: var(--sakura-500);
            color: white;
        }}

        /* Route info badge */
        .route-badge {{
            position: fixed;
            bottom: 30px;
            left: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 20px;
            background: white;
            border-radius: 50px;
            box-shadow: var(--shadow-medium);
            z-index: 100;
        }}
        .route-badge-item {{
            text-align: center;
        }}
        .route-badge-value {{
            font-family: 'Quicksand', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: var(--brown-900);
        }}
        .route-badge-label {{
            font-size: 9px;
            color: var(--brown-800);
            opacity: 0.6;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .route-badge-divider {{
            width: 1px;
            height: 30px;
            background: var(--sakura-200);
        }}
    </style>
</head>
<body>
    <div class="petals-container" id="petals"></div>

    <!-- Start Page -->
    <div class="start-page" id="startPage">
        <div class="start-card">
            <div class="brand">NUST Navigator</div>
            <h1 class="start-title">Your Route is Ready</h1>
            
            <div class="route-visual">
                <div class="location-badge">
                    <div class="location-dot start">A</div>
                    <div class="location-name" title="{start_name}">{start_name[:15]}{'...' if len(start_name) > 15 else ''}</div>
                </div>
                <div class="route-line"></div>
                <div class="location-badge">
                    <div class="location-dot end">B</div>
                    <div class="location-name" title="{end_name}">{end_name[:15]}{'...' if len(end_name) > 15 else ''}</div>
                </div>
            </div>

            <div class="mode-badge">
                <span class="material-icons-round">{mode_icon}</span>
                {mode_display}
            </div>

            <div class="quick-stats">
                <div class="quick-stat">
                    <div class="quick-stat-value">{time_min:.1f}</div>
                    <div class="quick-stat-label">minutes</div>
                </div>
                <div class="quick-stat">
                    <div class="quick-stat-value">{distance_km:.2f}</div>
                    <div class="quick-stat-label">km</div>
                </div>
                <div class="quick-stat">
                    <div class="quick-stat-value">+{climb:.0f}</div>
                    <div class="quick-stat-label">m climb</div>
                </div>
            </div>

            <button class="explore-btn" onclick="showMap()">
                View on Map
                <span class="material-icons-round">map</span>
            </button>

            <div class="generated-time">{current_time}</div>
        </div>
    </div>

    <!-- Map View -->
    <div class="map-view" id="mapView">
        <div id="map"></div>
        
        <!-- POI Filter Popup -->
        <div class="poi-filter-overlay" id="poiFilterOverlay" onclick="closePoiFilter()"></div>
        <div class="poi-filter-popup" id="poiFilterPopup">
            <div class="poi-popup-header">
                <button class="poi-popup-close" onclick="closePoiFilter()">
                    <span class="material-icons-round">close</span>
                </button>
                <h3><span class="material-icons-round">filter_list</span> Filter POIs</h3>
                <p>Select which points of interest to display</p>
            </div>
            <div class="poi-popup-actions">
                <button class="poi-action-btn" onclick="selectAllPois()">
                    <span class="material-icons-round">done_all</span>
                    Select All
                </button>
                <button class="poi-action-btn" onclick="selectNonePois()">
                    <span class="material-icons-round">remove_done</span>
                    Clear All
                </button>
            </div>
            <div class="poi-popup-list" id="poiCategoryList">
                <!-- Categories will be populated by JS -->
            </div>
        </div>
        
        <!-- FIXED: Left side controls group -->
        <div class="left-controls">
            <button class="control-btn" onclick="showStart()">
                <span class="material-icons-round">arrow_back</span>
                Back
            </button>
            <button class="control-btn" id="togglePoisBtn" onclick="openPoiFilter()">
                <span class="material-icons-round">place</span>
                POIs
            </button>
            
            <!-- Map Type Selector -->
            <div class="map-type-group">
                <button class="map-type-btn active" id="mapTypeRoadmap" onclick="setMapType('roadmap')">
                    <span class="material-icons-round">map</span>
                </button>
                <button class="map-type-btn" id="mapTypeSatellite" onclick="setMapType('satellite')">
                    <span class="material-icons-round">satellite_alt</span>
                </button>
                <button class="map-type-btn" id="mapTypeTerrain" onclick="setMapType('terrain')">
                    <span class="material-icons-round">terrain</span>
                </button>
                <button class="map-type-btn" id="mapTypeHybrid" onclick="setMapType('hybrid')">
                    <span class="material-icons-round">layers</span>
                </button>
            </div>
        </div>

        <!-- FIXED: Bottom route summary badge -->
        <div class="route-badge">
            <div class="route-badge-item">
                <div class="route-badge-value">{time_min:.1f} min</div>
                <div class="route-badge-label">Duration</div>
            </div>
            <div class="route-badge-divider"></div>
            <div class="route-badge-item">
                <div class="route-badge-value">{distance_km:.2f} km</div>
                <div class="route-badge-label">Distance</div>
            </div>
            <div class="route-badge-divider"></div>
            <div class="route-badge-item">
                <div class="route-badge-value">{energy_value}</div>
                <div class="route-badge-label">{energy_label}</div>
            </div>
        </div>

        <!-- FIXED: Right panels with proper constraints -->
        <div class="panel-container">
            <!-- Algorithm Panel (most impressive, show first) -->
            <div class="panel" id="panelAlgo">
                <div class="panel-header" onclick="togglePanel('panelAlgo')">
                    <div class="panel-title">
                        <span class="material-icons-round">memory</span>
                        Algorithm
                    </div>
                    <span class="material-icons-round panel-toggle">expand_more</span>
                </div>
                <div class="panel-content">
                    <div class="algo-card">
                        <div class="algo-name">{algo_name}</div>
                        <div class="algo-stats">
                            <div class="algo-stat"><strong>{nodes_explored:,}</strong> nodes</div>
                            <div class="algo-stat"><strong>{heap_ops:,}</strong> heap ops</div>
                            <div class="algo-stat"><strong>{compute_time:.1f}</strong> ms</div>
                        </div>
                        {f'<div class="algo-stats" style="margin-top:8px;"><div class="algo-stat"><strong>{a_star_calls}</strong> A* calls</div><div class="algo-stat"><strong>{permutations_checked}</strong> perms</div></div>' if a_star_calls > 0 else ''}
                    </div>
                </div>
            </div>

            <!-- Elevation Panel -->
            <div class="panel" id="panelElevation">
                <div class="panel-header" onclick="togglePanel('panelElevation')">
                    <div class="panel-title">
                        <span class="material-icons-round">terrain</span>
                        Elevation
                    </div>
                    <span class="material-icons-round panel-toggle">expand_more</span>
                </div>
                <div class="panel-content">
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-value" style="color:#10B981">+{climb:.0f}</div>
                            <div class="stat-label">Climb (m)</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" style="color:#EF4444">-{descent:.0f}</div>
                            <div class="stat-label">Descent (m)</div>
                        </div>
                    </div>
                    <div class="elevation-chart">
                        <svg class="elevation-svg" id="elevationSvg" viewBox="0 0 280 45" preserveAspectRatio="none">
                            <defs>
                                <linearGradient id="elevationGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                    <stop offset="0%" style="stop-color:#E75480;stop-opacity:0.4" />
                                    <stop offset="100%" style="stop-color:#E75480;stop-opacity:0" />
                                </linearGradient>
                            </defs>
                        </svg>
                    </div>
                    <div class="elevation-labels">
                        <span>Start</span>
                        <span>End</span>
                    </div>
                </div>
            </div>

            <!-- POIs Panel -->
            <div class="panel" id="panelPois">
                <div class="panel-header" onclick="togglePanel('panelPois')">
                    <div class="panel-title">
                        <span class="material-icons-round">near_me</span>
                        Nearby
                    </div>
                    <span class="material-icons-round panel-toggle">expand_more</span>
                </div>
                <div class="panel-content">
                    {pois_html}
                </div>
            </div>

            <!-- Fun Stats Panel -->
            <div class="panel" id="panelFun">
                <div class="panel-header" onclick="togglePanel('panelFun')">
                    <div class="panel-title">
                        <span class="material-icons-round">emoji_events</span>
                        Fun Facts
                    </div>
                    <span class="material-icons-round panel-toggle">expand_more</span>
                </div>
                <div class="panel-content">
                    {fun_stats_html}
                </div>
            </div>
        </div>
    </div>

    <script>
        const routeCoords = {route_coords_json};
        const elevations = {elevation_json};
        const startCoord = {json.dumps(start_coord)};
        const endCoord = {json.dumps(end_coord)};
        const alternativeRoutes = {alternatives_js};
        const multiStopSegments = {multi_stop_js};
        const waypoints = {waypoints_js};
        const poiData = {pois_js};
        
        // Colors for multi-stop route segments
        const segmentColors = ['#E75480', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4'];

        let map, routePolyline, altPolylines = [], poiMarkers = [], segmentPolylines = [], waypointMarkers = [];
        let poisVisible = false;

        function createPetals() {{
            const container = document.getElementById('petals');
            for (let i = 0; i < 25; i++) {{
                const petal = document.createElement('div');
                petal.className = 'petal';
                petal.style.left = Math.random() * 100 + 'vw';
                petal.style.animationDuration = (Math.random() * 6 + 10) + 's';
                petal.style.animationDelay = (Math.random() * 15) + 's';
                container.appendChild(petal);
            }}
        }}
        createPetals();

        function showMap() {{
            document.getElementById('startPage').classList.add('hidden');
            document.getElementById('mapView').classList.add('active');
            setTimeout(initMap, 300);
        }}

        function showStart() {{
            document.getElementById('startPage').classList.remove('hidden');
            document.getElementById('mapView').classList.remove('active');
        }}

        function togglePanel(id) {{
            document.getElementById(id).classList.toggle('collapsed');
        }}

        // POI Filter System
        const poiStyles = {{
            'fuel': {{ color: '#EF4444', icon: '⛽', bg: '#FEE2E2' }},
            'restaurant': {{ color: '#F97316', icon: '🍽️', bg: '#FFEDD5' }},
            'fast_food': {{ color: '#FBBF24', icon: '🍔', bg: '#FEF3C7' }},
            'cafe': {{ color: '#A16207', icon: '☕', bg: '#FEF3C7' }},
            'university': {{ color: '#8B5CF6', icon: '🎓', bg: '#EDE9FE' }},
            'library': {{ color: '#3B82F6', icon: '📚', bg: '#DBEAFE' }},
            'parking': {{ color: '#6B7280', icon: '🅿️', bg: '#F3F4F6' }},
            'hospital': {{ color: '#DC2626', icon: '🏥', bg: '#FEE2E2' }},
            'pharmacy': {{ color: '#10B981', icon: '💊', bg: '#D1FAE5' }},
            'bank': {{ color: '#059669', icon: '🏦', bg: '#D1FAE5' }},
            'atm': {{ color: '#14B8A6', icon: '💳', bg: '#CCFBF1' }},
            'hotel': {{ color: '#EC4899', icon: '🏨', bg: '#FCE7F3' }},
            'mosque': {{ color: '#22C55E', icon: '🕌', bg: '#DCFCE7' }},
            'police': {{ color: '#1E40AF', icon: '👮', bg: '#DBEAFE' }},
            'marketplace': {{ color: '#F59E0B', icon: '🛒', bg: '#FEF3C7' }},
            'landmark': {{ color: '#8B5CF6', icon: '🏛️', bg: '#EDE9FE' }},
            'default': {{ color: '#F59E0B', icon: '📍', bg: '#FEF3C7' }}
        }};
        
        let selectedCategories = new Set();
        let poiByCategory = {{}};
        
        function initPoiCategories() {{
            // Group POIs by category
            poiByCategory = {{}};
            poiData.forEach((poi, idx) => {{
                const cat = poi.type || 'default';
                if (!poiByCategory[cat]) poiByCategory[cat] = [];
                poiByCategory[cat].push(idx);
            }});
            
            // Select all categories by default
            selectedCategories = new Set(Object.keys(poiByCategory));
            
            // Build category list UI
            const listEl = document.getElementById('poiCategoryList');
            listEl.innerHTML = '';
            
            Object.keys(poiByCategory).sort().forEach(cat => {{
                const style = poiStyles[cat] || poiStyles['default'];
                const count = poiByCategory[cat].length;
                
                const item = document.createElement('div');
                item.className = 'poi-category-item selected';
                item.dataset.category = cat;
                item.onclick = () => toggleCategory(cat);
                
                item.innerHTML = `
                    <div class="poi-category-icon" style="background: ${{style.bg}}">
                        ${{style.icon}}
                    </div>
                    <div class="poi-category-info">
                        <div class="poi-category-name">${{cat.replace('_', ' ')}}</div>
                        <div class="poi-category-count">${{count}} location${{count !== 1 ? 's' : ''}}</div>
                    </div>
                    <div class="poi-category-check">
                        <span class="material-icons-round" style="font-size: 16px;">check</span>
                    </div>
                `;
                
                listEl.appendChild(item);
            }});
        }}
        
        function toggleCategory(cat) {{
            if (selectedCategories.has(cat)) {{
                selectedCategories.delete(cat);
            }} else {{
                selectedCategories.add(cat);
            }}
            updateCategoryUI();
            applyPoiFilter();
        }}
        
        function selectAllPois() {{
            selectedCategories = new Set(Object.keys(poiByCategory));
            updateCategoryUI();
            applyPoiFilter();
        }}
        
        function selectNonePois() {{
            selectedCategories.clear();
            updateCategoryUI();
            applyPoiFilter();
        }}
        
        function updateCategoryUI() {{
            document.querySelectorAll('.poi-category-item').forEach(item => {{
                const cat = item.dataset.category;
                if (selectedCategories.has(cat)) {{
                    item.classList.add('selected');
                }} else {{
                    item.classList.remove('selected');
                }}
            }});
            
            // Update main button state
            const anyVisible = selectedCategories.size > 0;
            document.getElementById('togglePoisBtn').classList.toggle('active', anyVisible);
        }}
        
        function applyPoiFilter() {{
            poiMarkers.forEach((marker, idx) => {{
                const poi = poiData[idx];
                const cat = poi.type || 'default';
                marker.setVisible(selectedCategories.has(cat));
            }});
        }}
        
        function openPoiFilter() {{
            document.getElementById('poiFilterOverlay').classList.add('active');
            document.getElementById('poiFilterPopup').classList.add('active');
        }}
        
        function closePoiFilter() {{
            document.getElementById('poiFilterOverlay').classList.remove('active');
            document.getElementById('poiFilterPopup').classList.remove('active');
        }}

        function togglePOIs() {{
            poisVisible = !poisVisible;
            document.getElementById('togglePoisBtn').classList.toggle('active', poisVisible);
            poiMarkers.forEach(m => m.setVisible(poisVisible));
        }}

        function setMapType(type) {{
            if (!map) return;
            
            // Update button states
            document.querySelectorAll('.map-type-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('mapType' + type.charAt(0).toUpperCase() + type.slice(1)).classList.add('active');
            
            // Set map type
            map.setMapTypeId(google.maps.MapTypeId[type.toUpperCase()]);
            
            // Adjust route styling for satellite/hybrid views
            if (type === 'satellite' || type === 'hybrid') {{
                routePolyline.setOptions({{ strokeColor: '#FF69B4', strokeWeight: 6, strokeOpacity: 1.0 }});
            }} else {{
                routePolyline.setOptions({{ strokeColor: '#E75480', strokeWeight: 5, strokeOpacity: 1.0 }});
            }}
        }}

        function initMap() {{
            if (map) return;

            map = new google.maps.Map(document.getElementById('map'), {{
                zoom: 15,
                center: {{ lat: (startCoord.lat + endCoord.lat) / 2, lng: (startCoord.lng + endCoord.lng) / 2 }},
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                styles: [
                    {{ featureType: "poi", stylers: [{{ visibility: "simplified" }}] }},
                    {{ featureType: "poi.business", stylers: [{{ visibility: "off" }}] }},
                    {{ featureType: "transit", stylers: [{{ visibility: "simplified" }}] }},
                    {{ featureType: "water", stylers: [{{ color: "#E0F2FE" }}] }},
                    {{ featureType: "landscape", stylers: [{{ color: "#FAFAFA" }}] }},
                    {{ featureType: "road", elementType: "geometry", stylers: [{{ color: "#FFFFFF" }}] }},
                    {{ featureType: "road", elementType: "geometry.stroke", stylers: [{{ color: "#E5E7EB" }}] }},
                    {{ featureType: "road", elementType: "labels.text.fill", stylers: [{{ color: "#6B7280" }}] }},
                    {{ featureType: "road.highway", elementType: "geometry", stylers: [{{ color: "#FFE4E1" }}] }},
                    {{ featureType: "road.highway", elementType: "geometry.stroke", stylers: [{{ color: "#FFB6C1" }}] }}
                ],
                disableDefaultUI: false,
                zoomControl: true,
                zoomControlOptions: {{ position: google.maps.ControlPosition.LEFT_BOTTOM }},
                mapTypeControl: false,
                streetViewControl: true,
                streetViewControlOptions: {{ position: google.maps.ControlPosition.LEFT_BOTTOM }},
                fullscreenControl: true,
                fullscreenControlOptions: {{ position: google.maps.ControlPosition.TOP_LEFT }},
                scaleControl: true,
                rotateControl: true
            }});

            // Check if multi-stop route
            if (multiStopSegments && multiStopSegments.length > 0) {{
                // Draw each segment with a different color
                multiStopSegments.forEach((segment, idx) => {{
                    const color = segmentColors[idx % segmentColors.length];
                    const segPoly = new google.maps.Polyline({{
                        path: segment,
                        geodesic: true,
                        strokeColor: color,
                        strokeOpacity: 1.0,
                        strokeWeight: 6,
                        map: map
                    }});
                    segmentPolylines.push(segPoly);
                }});
                
                // Draw waypoint markers with numbers
                waypoints.forEach((wp, idx) => {{
                    const label = idx === 0 ? 'S' : idx.toString();
                    const color = idx === 0 ? '#10B981' : segmentColors[(idx - 1) % segmentColors.length];
                    createMarker(wp.coord, label, color, wp.label);
                }});
            }} else {{
                // Single route - draw normally
                routePolyline = new google.maps.Polyline({{
                    path: routeCoords,
                    geodesic: true,
                    strokeColor: '#E75480',
                    strokeOpacity: 1.0,
                    strokeWeight: 5,
                    map: map
                }});

                // Alternative routes
                alternativeRoutes.forEach((alt, idx) => {{
                    const altPoly = new google.maps.Polyline({{
                        path: alt.coords,
                        geodesic: true,
                        strokeColor: '#9CA3AF',
                        strokeOpacity: 0.5,
                        strokeWeight: 4,
                        map: map
                    }});
                    altPolylines.push(altPoly);
                }});

                // Markers for single route
                createMarker(startCoord, 'A', '#10B981');
                createMarker(endCoord, 'B', '#E75480');
            }}

            // Fit bounds with padding for panels
            const bounds = new google.maps.LatLngBounds();
            routeCoords.forEach(c => bounds.extend(c));
            map.fitBounds(bounds, {{ top: 50, right: 340, bottom: 100, left: 50 }});

            // Create POI markers (visible by default since all categories selected)
            poiData.forEach((poi, idx) => {{
                if (poi.lat && poi.lng) {{
                    const style = poiStyles[poi.type] || poiStyles['default'];
                    const marker = new google.maps.Marker({{
                        position: {{ lat: poi.lat, lng: poi.lng }},
                        map: map,
                        visible: true,  // All visible by default
                        icon: {{
                            path: google.maps.SymbolPath.BACKWARD_CLOSED_ARROW,
                            scale: 6,
                            fillColor: style.color,
                            fillOpacity: 0.9,
                            strokeColor: '#FFFFFF',
                            strokeWeight: 2
                        }},
                        title: poi.name + ' (' + poi.type + ')'
                    }});
                    
                    const infoWindow = new google.maps.InfoWindow({{
                        content: `<div style="font-family: 'Quicksand', sans-serif; padding: 8px;">
                            <span style="font-size: 20px;">${{style.icon}}</span>
                            <strong style="color: ${{style.color}}">${{poi.name}}</strong><br>
                            <span style="color: #6B7280; font-size: 12px; text-transform: capitalize;">${{poi.type ? poi.type.replace('_', ' ') : 'Location'}}</span><br>
                            <span style="color: #10B981; font-size: 11px;">${{poi.distance_m ? (poi.distance_m / 1000).toFixed(2) + ' km away' : ''}}</span>
                        </div>`
                    }});
                    marker.addListener('click', () => infoWindow.open(map, marker));
                    
                    poiMarkers.push(marker);
                }}
            }});

            // Initialize POI category filter
            initPoiCategories();
            document.getElementById('togglePoisBtn').classList.add('active');

            drawElevationChart();
        }}

        function createMarker(coord, label, color, title = '') {{
            const marker = new google.maps.Marker({{
                position: coord,
                map: map,
                label: {{ text: label, color: 'white', fontWeight: 'bold', fontSize: '14px' }},
                icon: {{
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 16,
                    fillColor: color,
                    fillOpacity: 1,
                    strokeColor: 'white',
                    strokeWeight: 3
                }},
                title: title
            }});
            
            // Add info window for multi-stop waypoints
            if (title) {{
                const infoWindow = new google.maps.InfoWindow({{
                    content: `<div style="font-family: 'Quicksand', sans-serif; padding: 8px;">
                        <strong style="color: ${{color}}">${{label === 'S' ? 'Start' : 'Stop ' + label}}</strong><br>
                        <span>${{title}}</span>
                    </div>`
                }});
                marker.addListener('click', () => infoWindow.open(map, marker));
            }}
            
            return marker;
        }}

        function drawElevationChart() {{
            if (elevations.length < 2) return;

            const svg = document.getElementById('elevationSvg');
            const width = 280;
            const height = 45;
            const padTop = 5;
            const padBottom = 5;

            const minElev = Math.min(...elevations);
            const maxElev = Math.max(...elevations);
            const elevRange = maxElev - minElev || 1;

            let pathD = 'M ';
            let fillD = `M 0 ${{height}} L `;

            elevations.forEach((elev, i) => {{
                const x = (i / (elevations.length - 1)) * width;
                const y = height - padBottom - ((elev - minElev) / elevRange) * (height - padTop - padBottom);
                pathD += `${{x}},${{y}} `;
                fillD += `${{x}},${{y}} `;
            }});

            fillD += `L ${{width}} ${{height}} Z`;

            const fillEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            fillEl.setAttribute('d', fillD);
            fillEl.setAttribute('class', 'elevation-fill');
            svg.appendChild(fillEl);

            const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            pathEl.setAttribute('d', pathD);
            pathEl.setAttribute('class', 'elevation-path');
            svg.appendChild(pathEl);
        }}
    </script>
</body>
</html>'''
