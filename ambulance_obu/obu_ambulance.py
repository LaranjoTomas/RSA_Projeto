import json
import time
import math
import paho.mqtt.client as mqtt

# === Configuration ===
MQTT_BROKER = "192.168.98.20"
MQTT_PORT = 1883
CAM_MQTT_TOPIC = "vanetza/in/cam"
CAM_FILE_PATH = "obu_cam.json"
DENM_MQTT_TOPIC = "vanetza/in/denm"
DENM_FILE_PATH = "obu_denm.json"
LANE_FILE_PATH = "lane_coordinates_with_n.json"
PUBLISH_INTERVAL = 0.1


INTERSECTION_CENTER = {"lat": 40.6329, "lng": -8.6585}
DENM_THRESHOLD = 100  # when within X sends denm

# === Tracking ===
denm_counter = 0
current_lane = 4
lane_point = 0

# === Compute Start Positions ===
def meters_to_lat(dm):
    return (dm / 6371000) * (180 / math.pi)

def meters_to_lng(dm, lat):
    return (dm / (6371000 * math.cos(math.radians(lat)))) * (180 / math.pi)

NS_START = 300   # north/south roads
EW_START = 500   # east/west roads

position = {
    1: {  # Northbound starts north of intersection
        "lat": INTERSECTION_CENTER["lat"] + meters_to_lat(NS_START),
        "lng": INTERSECTION_CENTER["lng"]
    },
    3: {  # Southbound starts south of intersection
        "lat": INTERSECTION_CENTER["lat"] - meters_to_lat(NS_START),
        "lng": INTERSECTION_CENTER["lng"]
    },
    2: {  # Eastbound starts east of intersection
        "lat": INTERSECTION_CENTER["lat"],
        "lng": INTERSECTION_CENTER["lng"] + meters_to_lng(EW_START, INTERSECTION_CENTER["lat"])
    },
    4: {  # Westbound starts west of intersection
        "lat": INTERSECTION_CENTER["lat"],
        "lng": INTERSECTION_CENTER["lng"] - meters_to_lng(EW_START, INTERSECTION_CENTER["lat"])
    }
}

speed_delta = 0.000030
last_dist = None
denm_sent = False

# === Utility Functions ===

def load_json(filepath):
    with open(filepath, "r") as file:
        return json.load(file)

def haversine_distance(lat1, lon1, lat2, lon2):
    # Calculate distance in meters between two lat/lon pairs
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# === CAM ===

def update_cam_position(cam_msg, lane):
    pos = position[lane]

    if lane == 1:  # North: move south (decrease latitude)
        pos["lat"] -= speed_delta
    elif lane == 2:  # East: move west (decrease longitude)
        pos["lng"] -= speed_delta
    elif lane == 3:  # South: move north (increase latitude)
        pos["lat"] += speed_delta
    elif lane == 4:  # West: move east (increase longitude)
        pos["lng"] += speed_delta

    # Set updated values in cam_msg with a small fixed heading per lane
    if lane == 1:
        cam_msg["latitude"] = pos["lat"]
        cam_msg["longitude"] = pos["lng"]
        cam_msg["heading"] = 180  # Moving south
    elif lane == 2:
        cam_msg["latitude"] = pos["lat"]
        cam_msg["longitude"] = pos["lng"]
        cam_msg["heading"] = 270  # Moving west
    elif lane == 3:
        cam_msg["latitude"] = pos["lat"]
        cam_msg["longitude"] = pos["lng"]
        cam_msg["heading"] = 0    # Moving north
    elif lane == 4:
        cam_msg["latitude"] = pos["lat"]
        cam_msg["longitude"] = pos["lng"]
        cam_msg["heading"] = 90   # Moving east

    # Mark as emergency vehicle
    cam_msg["stationType"] = 10
    # Optionally include a speed field
    cam_msg["speed"] = 80
    return cam_msg

def publish_cam():
    cam_msg = load_json(CAM_FILE_PATH)

    cam_msg = update_cam_position(cam_msg, current_lane)
    cam_msg["generationDeltaTime"] = (int(time.time() * 1000) % 65536)

    payload = json.dumps(cam_msg)

    info = client.publish(CAM_MQTT_TOPIC, payload)
    # check .rc, not result[0]
    if info.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Sent CAM message to `{CAM_MQTT_TOPIC}`: pos=({cam_msg['latitude']:.7f}, {cam_msg['longitude']:.7f})")
    else:
        print(f"Failed to send CAM to `{CAM_MQTT_TOPIC}` (rc={info.rc})")

# === DENM ===

def publish_denm():
    denm_msg = load_json(DENM_FILE_PATH)
    pos = position[current_lane]
    heading = {1:180, 2:270, 3:0, 4:90}[current_lane]
    denm_msg["location"] = {
        "eventPositionHeading": heading,
        "eventPosition": {
            "latitude": pos["lat"],
            "longitude": pos["lng"]
        }
    }
    payload = json.dumps(denm_msg)
    info = client.publish(DENM_MQTT_TOPIC, payload)
    if info.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Sent DENM to `{DENM_MQTT_TOPIC}` (heading={heading})")
    else:
        print(f"Failed to send DENM to `{DENM_MQTT_TOPIC}` (rc={info.rc})")


# === MQTT Setup ===
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print("Failed to connect, return code %d\n", rc)

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# === Main Loop ===        
last_dist = None

if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            publish_cam()
            # compute distance
            cam_pos = position[current_lane]
            dist = haversine_distance(cam_pos["lat"], cam_pos["lng"],
                                      INTERSECTION_CENTER["lat"], INTERSECTION_CENTER["lng"])
            print(f"Distance from intersection: {dist:.1f} m (lane {current_lane})")

            # end-of-street threshold by lane orientation
            if current_lane in (2, 4):   # east/west
                end_threshold = EW_START
            else:                        # north/south
               end_threshold = NS_START

            if dist > end_threshold:
                cycle_order = [1, 4, 2, 3]
                idx = cycle_order.index(current_lane)
                current_lane = cycle_order[(idx + 1) % len(cycle_order)]
                denm_sent = False
                last_dist = None
                print(f"Cycling to next lane: {current_lane}")


            # DENM logic (unchanged)
            if last_dist is None:
                last_dist = dist

            if dist < DENM_THRESHOLD and dist <= last_dist and not denm_sent:
                publish_denm(); denm_sent = True
                print(f"DENM sent at {dist:.1f} m")
            if denm_sent and dist > last_dist + 5:
                denm_sent = False
                print("Reset DENM flag (moving away)")

            last_dist = dist
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
