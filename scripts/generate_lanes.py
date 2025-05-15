import numpy as np
import matplotlib.pyplot as plt
import json

# Lane width and desired spacing
lane_width = 2.0  # meters
point_spacing = 0.5  # meters

# Helper to generate straight line lane points
def generate_straight(start, end, spacing=0.5):
    distance = np.linalg.norm(np.array(end) - np.array(start))
    num_points = int(np.ceil(distance / spacing)) + 1
    x_vals = np.linspace(start[0], end[0], num_points)
    y_vals = np.linspace(start[1], end[1], num_points)
    return list(zip(x_vals, y_vals))

# Helper to generate arc lane points
def generate_arc(center, radius, start_angle, end_angle, spacing=0.5, clockwise=False):
    if clockwise:
        if end_angle > start_angle:
            end_angle -= 2 * np.pi
        arc_length = abs(end_angle - start_angle) * radius
        num_points = int(np.ceil(arc_length / spacing)) + 1
        angles = np.linspace(start_angle, end_angle, num_points)
    else:
        if end_angle < start_angle:
            end_angle += 2 * np.pi
        arc_length = abs(end_angle - start_angle) * radius
        num_points = int(np.ceil(arc_length / spacing)) + 1
        angles = np.linspace(start_angle, end_angle, num_points)
    return [(center[0] + radius * np.cos(a), center[1] + radius * np.sin(a)) for a in angles]

# L1: Loop (West inner loop), inner radius = 5m
lane1 = generate_arc((-6, -6), 5, -np.pi/2, np.pi/2, point_spacing, True)
# L1: Straight Part (bottom left horizontal lane, centerline at y = -1)
lane1 += generate_straight((-6, -1), (-2, -1), point_spacing)


# L2: Straight Part (bottom right horizontal lane, centerline at y = -1)
lane2 = generate_straight((-1.5, -1), (6, -1), point_spacing)
# L2: Loop (North outer loop), outer radius = 7m
lane2 += generate_arc((6, 6), 7, -np.pi/2, 0, point_spacing, False)


# L3: Loop (East outer loop), outer radius = 7m
lane3 = generate_arc((6, 6), 7, 0, -np.pi, point_spacing, False)
# L3: Straight Part (top left vertical lane, centerline at x = -1)
lane3 += generate_straight((-1, 6), (-1, 2), point_spacing)


# L4: Straight Part (bottom left vertical lane, centerline at x = -1)
lane4 = generate_straight((-1, 1.5), (-1, -6), point_spacing)
# L4: Loop (South inner loop), outer radius = 5m
lane4 += generate_arc((-6, -6), 5, 0, -np.pi/2, point_spacing, True)


# L5: Loop (East inner loop), inner radius = 5m
lane5 = generate_arc((6, 6), 5, np.pi/2, -np.pi/2, point_spacing, True)
# L5: Straight Part (top right horizontal lane, centerline at y = 1)
lane5 += generate_straight((6, 1), (2, 1), point_spacing)


# L6: Straight Part (top left horizontal lane, centerline at y = 1)
lane6 = generate_straight((1.5, 1), (-6, 1), point_spacing)
# L6: Loop (West outer loop), outer radius = 7m
lane6 += generate_arc((-6, -6), 7, np.pi/2, np.pi, point_spacing, False)


# L7: Loop (South outer loop), outer radius = 7m
lane7 = generate_arc((-6, -6), 7, -np.pi, 0, point_spacing, False)
# L7: Straight Part (top left vertical lane, centerline at x = 1)
lane7 += generate_straight((1, -6), (1, -2), point_spacing)


# L8: Straight Part (top right vertical lane, centerline at x = 1)
lane8 = generate_straight((1, -1.5), (1, 6), point_spacing)
# L8: Loop (North inner loop), inner radius = 5m
lane8 += generate_arc((6, 6), 5, -np.pi, np.pi/2, point_spacing, True)


# Assemble all intodictionary
lanes = {
    "L1": [{"x": x, "y": y} for x, y in lane1],
    "L2": [{"x": x, "y": y} for x, y in lane2],
    "L3": [{"x": x, "y": y} for x, y in lane3],
    "L4": [{"x": x, "y": y} for x, y in lane4],
    "L5": [{"x": x, "y": y} for x, y in lane5],
    "L6": [{"x": x, "y": y} for x, y in lane6],
    "L7": [{"x": x, "y": y} for x, y in lane7],
    "L8": [{"x": x, "y": y} for x, y in lane8],
}

# Save to JSON
with open("lane_coordinates.json", "w") as f:
    json.dump(lanes, f, indent=4)

print("Lane coordinates saved to lane_coordinates.json")

# Plot updated lanes
lanes = [lane1, lane2, lane3, lane4, lane5, lane6, lane7, lane8]
colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'brown', 'magenta']

plt.figure(figsize=(10, 10))
for i, lane in enumerate(lanes):
    x, y = zip(*lane)
    plt.plot(x, y, color=colors[i], label=f'Lane {i+1}')

plt.gca().set_aspect('equal')
plt.legend()
plt.title("Updated Lane Coordinates (Clockwise/Counter-Clockwise)")
plt.grid(True)
plt.show()
