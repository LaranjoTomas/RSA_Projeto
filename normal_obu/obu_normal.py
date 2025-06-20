import json
import time
import math
import paho.mqtt.client as mqtt
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# === Configuration ===
MQTT_BROKER = "192.168.98.30"  
MQTT_PORT = 1883
CAM_MQTT_TOPIC = "vanetza/in/cam"
CAM_FILE_PATH = "in_cam.json"
SPATEM_MQTT_TOPIC = "vanetza/out/spatem"  
PUBLISH_INTERVAL = 0.4
MAX_STOP_TIME = 10  

# === Tracking ===
current_lane = 1  
INTERSECTION_CENTER = {"lat": 40.6329, "lng": -8.6585}
INTERSECTION_THRESHOLD = 40
STOPPING_DISTANCE = 25  

# === Compute Start Positions ===
def meters_to_lat(dm):
    return (dm / 6371000) * (180 / math.pi)

def meters_to_lng(dm, lat):
    return (dm / (6371000 * math.cos(math.radians(lat)))) * (180 / math.pi)

NS_START = 300
EW_START = 500

LANE_OFFSET = 0.00010

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

speed_delta = 0.000045  
stopped_at_light = False
traffic_light_states = {
    0: "RED",    # North
    90: "RED",   # East
    180: "RED",  # South
    270: "RED",  # West
}

# === Utility Functions ===
def load_json(filepath):
    with open(filepath, "r") as file:
        return json.load(file)

def haversine_distance(lat1, lon1, lat2, lon2):
    # Calculate distance in meters between two lat/lon pairs
    R = 6371000  
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# === CAM ===
def update_cam_position(cam_msg, lane):
    global stopped_at_light
    pos = position[lane]

    if not stopped_at_light:
        if lane == 1:  # North: move south
            pos["lat"] -= speed_delta
        elif lane == 2:  # East: move west
            pos["lng"] -= speed_delta
        elif lane == 3:  # South: move north
            pos["lat"] += speed_delta
        elif lane == 4:  # West: move east
            pos["lng"] += speed_delta

    if lane == 1:
        cam_msg["latitude"] = pos["lat"]
        cam_msg["longitude"] = pos["lng"] - LANE_OFFSET
        cam_msg["heading"] = 180  # Moving south
    elif lane == 2:
        cam_msg["latitude"] = pos["lat"] + LANE_OFFSET
        cam_msg["longitude"] = pos["lng"]
        cam_msg["heading"] = 270  # Moving west
    elif lane == 3:
        cam_msg["latitude"] = pos["lat"]
        cam_msg["longitude"] = pos["lng"] + LANE_OFFSET
        cam_msg["heading"] = 0    # Moving north
    elif lane == 4:
        cam_msg["latitude"] = pos["lat"] - LANE_OFFSET
        cam_msg["longitude"] = pos["lng"]
        cam_msg["heading"] = 90   # Moving east

    cam_msg["stationType"] = 5
    cam_msg["speed"] = 0 if stopped_at_light else 80
    return cam_msg

def publish_cam():
    cam_msg = load_json(CAM_FILE_PATH)
    cam_msg = update_cam_position(cam_msg, current_lane)
    cam_msg["generationDeltaTime"] = (int(time.time() * 1000) % 65536)
    cam_msg["stationID"] = 3

    payload = json.dumps(cam_msg)
    info = client.publish(CAM_MQTT_TOPIC, payload)
    
    if info.rc == mqtt.MQTT_ERR_SUCCESS:
        status = "STOPPED" if stopped_at_light else "MOVING"
        print(f"Sent CAM message: pos=({cam_msg['latitude']:.7f}, {cam_msg['longitude']:.7f}) - {status}")
    else:
        print(f"Failed to send CAM (rc={info.rc})")

# === SPATEM Handler ===
def on_message(client, userdata, msg):
    global traffic_light_states, stopped_at_light
    
    print(f" RECEIVED MESSAGE ON TOPIC: {msg.topic}")
    
    try:
        spatem = json.loads(msg.payload.decode())
        print(f"SPATEM JSON: {json.dumps(spatem)}")
        
        signal_heading_map = {1: 0, 3: 90, 5: 180, 7: 270}
        
        if "intersections" in spatem.get("fields", {}).get("spat", {}):
            for intersection in spatem["fields"]["spat"]["intersections"]:
                for state in intersection.get("states", []):
                    signal_group = state.get("signalGroup")
                    print(f"Processing signal group: {signal_group}")
                    
                    if state.get("state-time-speed") and signal_group in signal_heading_map:
                        event_state = state["state-time-speed"][0].get("eventState")
                        heading = signal_heading_map[signal_group]
                        
                        light_state = "GREEN" if event_state == 5 else "RED"
                        
                        old_state = traffic_light_states.get(heading, "UNKNOWN")
                        if old_state != light_state:
                            print(f" Traffic light for {heading}° changed from {old_state} to {light_state}")
                        traffic_light_states[heading] = light_state
                        
                        print(f"Updated traffic light state: heading={heading}, state={light_state}")
    
    except Exception as e:
        print(f"Error processing SPATEM message: {e}")
        import traceback
        traceback.print_exc()

# === MQTT Setup ===
client = mqtt.Client(client_id=f"normal_obu_1", clean_session=False)
heading_map = {1: 0, 2: 90, 3: 180, 4: 270} 

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(SPATEM_MQTT_TOPIC, qos=0)
        logging.info("Subscribed to SPATEM topic with QoS=0")
    else:
        logging.error(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"Disconnected from broker with code {rc}")
    if rc != 0:
        logging.info("Attempting to reconnect...")
        time.sleep(2)
        try:
            client.reconnect()
        except Exception as e:
            logging.error(f"Reconnection failed: {e}")

def ensure_connection():
    """Ensure MQTT connection is active"""
    if not client.is_connected():
        logging.warning("Connection lost, attempting to reconnect...")
        try:
            client.reconnect()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Reconnection failed: {e}")
            return False
    return True

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

# === Main Loop ===
if __name__ == "__main__":
    print("====================== OBU Normal 1 ======================")
    client.loop_start()
    
    try:
        last_lane_switch_time = time.time()
        min_time_in_lane = 100
        
        logging.info(f"Initial position: {position[current_lane]}")
        logging.info(f"Publishing to topic: {CAM_MQTT_TOPIC}")
        logging.info(f"Listening for SPATEM on: {SPATEM_MQTT_TOPIC}")
        
        while True:
            if not ensure_connection():
                logging.warning("Not connected, skipping this cycle")
                time.sleep(1)
                continue
            
            cam_pos = position[current_lane]
            dist = haversine_distance(cam_pos["lat"], cam_pos["lng"],
                                    INTERSECTION_CENTER["lat"], INTERSECTION_CENTER["lng"])
            
            # Rest of your existing logic...
            if int(time.time() * 10) % 50 == 0:
                print(f"Position: lane={current_lane}, heading={heading_map[current_lane]}, " +
                      f"dist={dist:.1f}m, light={traffic_light_states.get(heading_map[current_lane], 'UNKNOWN')}")
                print(f"Current position: lat={cam_pos['lat']:.7f}, lng={cam_pos['lng']:.7f}")
                print(f"Stopped at light: {stopped_at_light}")
        
            current_heading = heading_map[current_lane]
            light_state = traffic_light_states.get(current_heading, "RED")
            
            if dist < INTERSECTION_THRESHOLD and dist > STOPPING_DISTANCE:
                if light_state == "RED" and not stopped_at_light:
                    stopped_at_light = True
                    print(f" Stopping at RED light, {dist:.1f}m from intersection")
                elif light_state == "GREEN":
                    stopped_at_light = False
                    if int(time.time() * 10) % 50 == 0:
                        print(f"Proceeding through GREEN light, {dist:.1f}m from intersection")
            elif dist <= STOPPING_DISTANCE:
                stopped_at_light = False
                if int(time.time() * 10) % 50 == 0:
                    print(f"Inside intersection zone")
            else:
                if stopped_at_light:
                    stopped_at_light = False
                    print("Far from intersection - resuming movement")
            
            publish_cam()
            
            current_time = time.time()
            time_since_switch = current_time - last_lane_switch_time
            
            if current_lane in (2, 4):
                end_threshold = 200
            else:
                end_threshold = 150

            if (time_since_switch > min_time_in_lane and 
                (dist > end_threshold or dist < 20)):
                if current_lane == 1:
                    current_lane = 4
                elif current_lane == 4:
                    current_lane = 1
                else:
                    current_lane = 1
                    
                stopped_at_light = False
                last_lane_switch_time = current_time
                print(f"Cycling to lane: {current_lane}")
                
                position[1]["lat"] = INTERSECTION_CENTER["lat"] + meters_to_lat(NS_START)
                position[1]["lng"] = INTERSECTION_CENTER["lng"]
                position[4]["lat"] = INTERSECTION_CENTER["lat"]
                position[4]["lng"] = INTERSECTION_CENTER["lng"] - meters_to_lng(EW_START, INTERSECTION_CENTER["lat"])
            
            time.sleep(PUBLISH_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()