import webbrowser
import os

# Your Google Maps API Key (Used for Frontend Visualization)
GOOGLE_API_KEY = "AIzaSyDjkvqozp-7DoEnMVS7kv1Rl4I80gDxjtc"

def generate_map(path_nodes, all_nodes, output_file="map.html"):
    """
    Generates a Google Maps visualization of the route.
    path_nodes: List of node IDs (strings or ints) from the algorithm.
    all_nodes: Dictionary of node data {id: {lat: x, lon: y...}}
    """
    
    # If only a filename is provided, save it to 'outputs/' in project root
    if os.path.dirname(output_file) == "":
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "outputs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, output_file)

    if not path_nodes or len(path_nodes) < 2:
        print("⚠️ Visualizer: Not enough nodes to plot a path.")
        return

    # 1. Extract Coordinates for the Route Polyline
    route_coords = []
    
    # Helper to safely get node data
    def get_node(nid):
        return all_nodes.get(str(nid)) or all_nodes.get(int(nid))

    for node_id in path_nodes:
        n = get_node(node_id)
        if n:
            route_coords.append(f"{{ lat: {n['lat']}, lng: {n['lon']} }}")
            
    start_node = get_node(path_nodes[0])
    end_node = get_node(path_nodes[-1])

    if not start_node or not end_node:
        print("⚠️ Visualizer: Could not find start/end node coordinates.")
        return

    # 2. Create HTML Content with Google Maps JS
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NUST Intelligent Navigation</title>
        <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_API_KEY}&libraries=places"></script>
        <style>
            body, html {{ height: 100%; margin: 0; font-family: 'Segoe UI', sans-serif; }}
            #map {{ height: 100%; width: 100%; }}
            #panel {{
                position: absolute; top: 20px; left: 20px; width: 320px;
                background: white; padding: 20px; border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); z-index: 100;
            }}
            h2 {{ margin: 0 0 10px 0; color: #004a99; font-size: 18px; }}
            .meta {{ font-size: 14px; color: #555; margin-bottom: 5px; }}
            .badge {{ 
                display: inline-block; background: #e3f2fd; color: #0d47a1; 
                padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div id="panel">
            <h2>NUST Navigation System</h2>
            <div class="meta"><span class="badge">ALGORITHM</span> Custom A* Search</div>
            <div class="meta"><span class="badge">DATA</span> Google Maps Elevation</div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 10px 0;">
            <p class="meta"><strong>Start:</strong> {start_node['lat']:.5f}, {start_node['lon']:.5f}</p>
            <p class="meta"><strong>End:</strong> {end_node['lat']:.5f}, {end_node['lon']:.5f}</p>
        </div>
        <div id="map"></div>

        <script>
            function initMap() {{
                const map = new google.maps.Map(document.getElementById("map"), {{
                    zoom: 16,
                    center: {{ lat: 33.6415, lng: 72.9910 }}, // NUST Center
                    mapTypeId: "roadmap",
                    styles: [
                        {{ featureType: "poi", elementType: "labels", stylers: [{{ visibility: "off" }}] }}
                    ]
                }});

                // The Path calculated by Python
                const routePath = [
                    {",".join(route_coords)}
                ];

                // Draw the Polyline
                const flightPath = new google.maps.Polyline({{
                    path: routePath,
                    geodesic: true,
                    strokeColor: "#2979FF",
                    strokeOpacity: 1.0,
                    strokeWeight: 5
                }});
                flightPath.setMap(map);

                // Start Marker
                new google.maps.Marker({{
                    position: routePath[0],
                    map: map,
                    label: "A",
                    title: "Start Point"
                }});

                // End Marker
                new google.maps.Marker({{
                    position: routePath[routePath.length - 1],
                    map: map,
                    label: "B",
                    title: "Destination"
                }});
                
                // Auto-zoom to fit route
                const bounds = new google.maps.LatLngBounds();
                routePath.forEach(pt => bounds.extend(pt));
                map.fitBounds(bounds);
            }}
            
            window.onload = initMap;
        </script>
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html_content)

    print(f"🗺️ Map Generated: {output_file}")
    try:
        webbrowser.open('file://' + os.path.realpath(output_file))
    except:
        pass