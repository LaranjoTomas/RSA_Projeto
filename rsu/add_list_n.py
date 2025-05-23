import json

with open("lane_coordinates.json", "r") as f:
    lanes = json.load(f)

for lane, points in lanes.items():
    for idx, pt in enumerate(points):
        pt["n"] = idx

with open("lane_coordinates_with_n.json", "w") as f:
    json.dump(lanes, f, indent=4)

print("Saved as lane_coordinates_with_n.json")