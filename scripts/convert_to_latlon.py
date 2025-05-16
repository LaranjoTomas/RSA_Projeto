import json

with open("lane_coordinates.json", "r") as f:
    lanes = json.load(f)

converted = {}

for lane_name, points in lanes.items():
    converted[lane_name] = []
    for pt in points:
        converted[lane_name].append({
            "delta": {
                "node-LatLon": {
                    "lat": pt["x"],
                    "lon": pt["y"]
                }
            }
        })

with open("lane_coordinates_latlon.json", "w") as f:
    json.dump(converted, f, indent=4)

print("Converted coordinates saved to lane_coordinates_latlon.json")