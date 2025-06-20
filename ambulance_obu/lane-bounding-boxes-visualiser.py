#!/usr/bin/env python3

import json
import math
import folium
import sys

############################################
# 1. Utility functions for coordinate math #
############################################

def meters_to_lat(meters: float) -> float:
    """
    Approx conversion: 1 degree latitude ~ 111,120 meters.
    """
    METERS_PER_DEG_LAT = 111120.0
    return meters / METERS_PER_DEG_LAT

def meters_to_lon(meters: float, lat_deg: float) -> float:
    """
    Approx conversion for longitude degrees, which vary by cos(latitude).
    """
    METERS_PER_DEG = 111120.0
    lat_rad = math.radians(lat_deg)
    cos_lat = math.cos(lat_rad)
    # Avoid division by zero if latitude is near +/- 90
    if abs(cos_lat) < 1e-12:
        cos_lat = 1e-12
    return meters / (METERS_PER_DEG * cos_lat)

def calculate_lane_rectangle(start, end, lane_width_meters):
    """
    Calculate the 4-corner rectangle for a lane segment from 'start' to 'end'
    with the specified lane width in meters.
    Returns a list of 4 corners (each corner is a (lat, lon) tuple).
    """

    (start_lat, start_lon) = start
    (end_lat, end_lon)     = end

    # 1) Mid-latitude for better longitude scaling
    mid_lat = (start_lat + end_lat) / 2.0

    # 2) Delta in lat/lon
    d_lat = end_lat - start_lat
    d_lon = end_lon - start_lon

    # 3) Angle of the segment w.r.t. east axis (longitude)
    #    Note that atan2 is (y, x) => (d_lat, d_lon)
    angle = math.atan2(d_lat, d_lon)

    # 4) Perp offset in (lat, lon) for half the lane width
    half_width = lane_width_meters / 2.0
    lat_offset = math.cos(angle) * meters_to_lat(half_width)
    lon_offset = -math.sin(angle) * meters_to_lon(half_width, mid_lat)

    # Build corners
    #   (corner0)---(corner3)
    #      ^          ^
    #      | +perp    | +perp
    #      start ----- end
    #      | -perp    | -perp
    #   (corner1)---(corner2)

    corner0 = (start_lat + lat_offset, start_lon + lon_offset)
    corner1 = (start_lat - lat_offset, start_lon - lon_offset)
    corner2 = (end_lat   - lat_offset, end_lon   - lon_offset)
    corner3 = (end_lat   + lat_offset, end_lon   + lon_offset)

    return [corner0, corner1, corner2, corner3]

############################################
# 2. JSON parsing and bounding-box building
############################################

def parse_lanes_from_json(json_data):
    """
    Given the loaded JSON data (with 'intersections'),
    extract lane data in the form:
        lanes_dict = {
           laneID: [(lat1,lon1), (lat2,lon2), ...],
           ...
        }
    Also extract the laneWidth (meters) from each intersection if present.
    For simplicity, we assume there's at least one intersection
    and a single laneWidth for all lanes in that intersection.
    """
    lanes_dict = {}
    lane_width_meters = 3.0  # fallback default

    intersections = json_data.get("intersections", [])
    if not intersections:
        print("No intersections in JSON!")
        return lanes_dict, lane_width_meters

    # We'll just look at the first intersection in the list for this example
    intersection = intersections[0]

    # Extract laneWidth from the intersection (if it exists)
    # The JSON calls it "laneWidth" and it looks like it's in decimeters or centimeters in some standards,
    # but the example shows a normal integer (like 4). We'll assume "4" means 4 meters or "400" deci-centimeters.
    lane_width_meters = intersection.get("laneWidth", 4.0)

    lane_set = intersection.get("laneSet", [])
    for lane_entry in lane_set:
        lane_id = lane_entry["laneID"]
        node_list = lane_entry["nodeList"]["nodes"]

        coords = []
        for node in node_list:
            lat = node["delta"]["node-LatLon"]["lat"]
            lon = node["delta"]["node-LatLon"]["lon"]
            coords.append((lat, lon))
        lanes_dict[lane_id] = coords

    return lanes_dict, lane_width_meters

def build_bounding_rectangles_for_lanes(lanes_dict, lane_width_meters):
    """
    For each lane in lanes_dict (laneID -> list of coordinates),
    build bounding rectangles for each pair of consecutive points.
    Returns:
        bounding_rects = {
            laneID: [ [corner0, corner1, corner2, corner3],
                      [corner0, corner1, corner2, corner3],
                      ... per lane ],
            ...
        }
    """
    bounding_rects = {}

    for lane_id, coords in lanes_dict.items():
        rects_for_lane = []
        # For each pair of consecutive coords
        for i in range(len(coords) - 1):
            start = coords[i]
            end   = coords[i+1]
            rect  = calculate_lane_rectangle(start, end, lane_width_meters)
            rects_for_lane.append(rect)
        bounding_rects[lane_id] = rects_for_lane

    return bounding_rects

##############################
# 3. Visualization with Folium
##############################

def visualize_lanes(bounding_rects):
    """
    Creates a Folium map, draws polygons for each bounding rectangle,
    and returns the Folium map object.
    """
    # Find some center for the map. We'll just pick
    # the average lat/lon of the first bounding rectangle we can find.
    # Or default to (40.0, -8.0) if none found.
    center_lat = 40.0
    center_lon = -8.0

    # Attempt to compute a rough center
    found_any = False
    for _, lane_rects in bounding_rects.items():
        if lane_rects:
            # Take the first rectangle of this lane, corner0
            corner0 = lane_rects[0][0]
            center_lat, center_lon = corner0
            found_any = True
            break

    folium_map = folium.Map(
        location=(center_lat, center_lon), 
        zoom_start=17, 
        max_zoom=24,
        tiles='http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        #tiles='https://stamen-tiles.a.ssl.fastly.net/toner-lite/{z}/{x}/{y}.png',
        attr='Google Satellite'

        )

    # Add polygons for each lane’s bounding rectangles
    colors = ["blue", "green", "red", "purple", "orange"]  # cycle through some colors
    color_index = 0

    for lane_id, lane_rects in bounding_rects.items():
        color = colors[color_index % len(colors)]
        color_index += 1

        # For each rectangle, add a polygon
        for rect in lane_rects:
            folium.Polygon(
                locations=rect,     # rect is already a list of (lat, lon) corners
                color=color,
                fill=True,
                fill_opacity=0.4,
                tooltip=f"Lane {lane_id}"
            ).add_to(folium_map)

    return folium_map

##########################
# 4. Main script workflow
##########################

def main():
    if len(sys.argv) < 2:
        print("Usage: python lane_bounding_boxes.py <path_to_json>")
        sys.exit(1)

    json_file = sys.argv[1]

    # 1) Load the JSON from file
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2) Parse out the lane coordinates and lane width
    lanes_dict, lane_width_meters = parse_lanes_from_json(data)

    if not lanes_dict:
        print("No lane data found. Exiting.")
        return

    print(f"Using lane width: {lane_width_meters} meters")

    # 3) Build oriented bounding rectangles for each lane
    bounding_rects = build_bounding_rectangles_for_lanes(lanes_dict, lane_width_meters)

    # Just print them out in console
    for lane_id, rects in bounding_rects.items():
        print(f"\nLane {lane_id} bounding rectangles:")
        for idx, rect in enumerate(rects):
            print(f"  Segment {idx} corners:")
            for c_i, corner in enumerate(rect):
                print(f"    Corner {c_i}: (lat={corner[0]}, lon={corner[1]})")

    # 4) Visualize on a Folium map
    folium_map = visualize_lanes(bounding_rects)

    # 5) Save to HTML
    output_file = json_file + ".html"
    folium_map.save(output_file)
    print(f"\nMap with lane bounding boxes saved to: {output_file}")

if __name__ == "__main__":
    main()