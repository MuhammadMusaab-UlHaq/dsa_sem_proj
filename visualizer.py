import json
import os
import webbrowser

def visualize_path(graph, path: list, pois: list = [], output_file: str = "map.html"):
    """
    Generates a modern MapLibre GL JS map using OpenFreeMap tiles.
    Overlays the Python-calculated A* path and POIs.
    """
    if not path:
        print("No path to visualize.")
        return

    # 1. Convert Path to GeoJSON LineString
    # MapLibre/GeoJSON expects [lon, lat], NOT [lat, lon]
    route_coords = []
    
    for i in range(len(path) - 1):
        u_id = path[i]
        v_id = path[i+1]
        
        # Get geometry from the edge data
        # neighbors list structure: (neighbor_id, weight, is_walk, is_drive, geometry)
        neighbors = graph.get_neighbors(u_id)
        edge_geometry = []
        
        found_edge = False
        for n in neighbors:
            if n[0] == v_id:
                edge_geometry = n[4] # This is stored as [[lat, lon], ...] in structures.py
                found_edge = True
                break
        
        if found_edge and edge_geometry:
            # Swap to [lon, lat] for GeoJSON
            segment = [[pt[1], pt[0]] for pt in edge_geometry]
            route_coords.extend(segment)
        else:
            # Fallback to straight line if geometry is missing
            n1 = graph.get_node(u_id)
            n2 = graph.get_node(v_id)
            if n1 and n2:
                route_coords.append([n1['lon'], n1['lat']])
                route_coords.append([n2['lon'], n2['lat']])

    # Handle single node path or start point
    if not route_coords and len(path) == 1:
        n = graph.get_node(path[0])
        route_coords.append([n['lon'], n['lat']])

    # 2. Prepare POIs as GeoJSON FeatureCollection
    poi_features = []
    for p in pois:
        poi_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [p['lon'], p['lat']]
            },
            "properties": {
                "name": p['name'],
                "type": p.get('type', 'POI')
            }
        })

    # 3. Calculate Map Center
    start_node = graph.get_node(path[0])
    center_lon = start_node['lon']
    center_lat = start_node['lat']

    # 4. Generate the HTML (Using MapLibre + OpenFreeMap Style)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>NUST Intelligent Navigation</title>
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
        <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
        <link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet" />
        <style>
            body {{ margin: 0; padding: 0; }}
            #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
            .legend {{
                background-color: #fff;
                border-radius: 3px;
                bottom: 30px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                font: 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;
                padding: 10px;
                position: absolute;
                right: 10px;
                z-index: 1;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="legend">
            <h4>Route Analytics</h4>
            <div><span style="background-color: #3b82f6; width: 10px; height: 10px; display: inline-block;"></span> Calculated Path</div>
            <div><span style="background-color: #ef4444; width: 10px; height: 10px; display: inline-block;"></span> POIs</div>
        </div>
        <script>
            const map = new maplibregl.Map({{
                container: 'map',
                style: 'https://tiles.openfreemap.org/styles/liberty', 
                center: [{center_lon}, {center_lat}],
                zoom: 14
            }});

            map.on('load', () => {{
                
                // LAYER 1: The Path
                map.addSource('route', {{
                    'type': 'geojson',
                    'data': {{
                        'type': 'Feature',
                        'properties': {{}},
                        'geometry': {{
                            'type': 'LineString',
                            'coordinates': {json.dumps(route_coords)}
                        }}
                    }}
                }});
                
                map.addLayer({{
                    'id': 'route',
                    'type': 'line',
                    'source': 'route',
                    'layout': {{
                        'line-join': 'round',
                        'line-cap': 'round'
                    }},
                    'paint': {{
                        'line-color': '#3b82f6',
                        'line-width': 6,
                        'line-opacity': 0.8
                    }}
                }});

                // LAYER 2: POIs
                map.addSource('pois', {{
                    'type': 'geojson',
                    'data': {{
                        'type': 'FeatureCollection',
                        'features': {json.dumps(poi_features)}
                    }}
                }});

                map.addLayer({{
                    'id': 'pois',
                    'type': 'circle',
                    'source': 'pois',
                    'paint': {{
                        'circle-radius': 8,
                        'circle-color': '#ef4444',
                        'circle-stroke-width': 2,
                        'circle-stroke-color': '#ffffff'
                    }}
                }});

                // Add popups on click for POIs
                map.on('click', 'pois', (e) => {{
                    const coordinates = e.features[0].geometry.coordinates.slice();
                    const name = e.features[0].properties.name;
                    new maplibregl.Popup()
                        .setLngLat(coordinates)
                        .setHTML('<strong>' + name + '</strong>')
                        .addTo(map);
                }});

                // Change cursor on hover
                map.on('mouseenter', 'pois', () => {{
                    map.getCanvas().style.cursor = 'pointer';
                }});
                map.on('mouseleave', 'pois', () => {{
                    map.getCanvas().style.cursor = '';
                }});
                
                // Fit bounds to route
                const coords = {json.dumps(route_coords)};
                if (coords.length > 0) {{
                    const bounds = coords.reduce((bounds, coord) => {{
                        return bounds.extend(coord);
                    }}, new maplibregl.LngLatBounds(coords[0], coords[0]));
                    map.fitBounds(bounds, {{ padding: 50 }});
                }}
            }});
        </script>
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html_content)
    
    print(f"Map generated: {output_file} (Using OpenFreeMap Tiles)")
    webbrowser.open('file://' + os.path.realpath(output_file))