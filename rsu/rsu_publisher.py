import json
import time
import copy
import paho.mqtt.client as mqtt

# === Configuration ===
MQTT_BROKER = "192.168.98.10"
MQTT_PORT = 1883
SPATEM_MQTT_TOPIC = "vanetza/time/spatem"
SPATEM_FILE_PATH = "rsu_spatem.json"
MAPEM_MQTT_TOPIC = "vanetza/time/mapem"
MAPEM_FILE_PATH = "rsu_mapem.json"
CAM_MQTT_TOPIC = "vanetza/time/cam"
CAM_FILE_PATH = "rsu_cam.json"
DENM_MQTT_TOPIC = "vanetza/out/denm" # Listening to the obu denm so it can change the semaphore lights to accomodate the emergency vehicle
PUBLISH_INTERVAL = 0.1  # seconds

# === Tracking ===
mapem_counter = 0   # publish mapem every 10 cam/spatem -> 1 Hz
lights = [0,0,0,0]

saved_normal_spatem = None
emergency_mode = False
emergency_mode_expiry = 0
emergency_target_signal = None

# === Load JSON ===
def load_json(filepath):
    with open(filepath, "r") as file:
        return json.load(file)

# === MQTT Setup ===
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print("Failed to connect, return code %d\n", rc)

client.on_connect = on_connect
client.connect(MQTT_BROKER, MQTT_PORT, 60)

client.subscribe("vanetza/out/denm")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        if topic == "vanetza/out/denm":
            print("Received DENM message from OBU")
            handle_emergency_denm(payload)
    except Exception as e:
        print("Error processing message: ", e)

client.on_message = on_message

# === DENM ===

def handle_emergency_denm(denm_payload):
    """
    Immediately set all semaphores to red and then set the semaphore for the lane 
    corresponding to the ambulance (determined from the DENM's heading) to green.
    """
    global emergency_mode, emergency_mode_expiry, emergency_target_signal
    emergency_duration = 10  # seconds for emergency mode to persist

    # Load the current SPATEM JSON template
    spatem_msg = load_json(SPATEM_FILE_PATH)
    
    # Set ALL semaphore states to RED (eventState=3) first
    for intr in spatem_msg.get("intersections", []):
        for state in intr.get("states", []):
            if state.get("state-time-speed"):
                state["state-time-speed"][0]["eventState"] = 3
                state["state-time-speed"][0]["timing"] = {"minEndTime": 30}
    
    # Determine the lane from the DENM's heading
    heading = denm_payload.get("location", {}).get("eventPositionHeading", 0)
    if heading >= 315 or heading < 45:
        target_signal = 1   # NORTH
    elif heading < 135:
        target_signal = 3   # EAST
    elif heading < 225:
        target_signal = 5   # SOUTH
    else:
        target_signal = 7   # WEST

    # Set emergency mode parameters
    emergency_mode = True
    emergency_mode_expiry = time.time() + emergency_duration
    emergency_target_signal = target_signal

    # AFTER setting all to RED, set ONLY the target semaphore to GREEN
    for intr in spatem_msg.get("intersections", []):
        for state in intr.get("states", []):
            if state.get("signalGroup") == target_signal and state.get("state-time-speed"):
                sts = state["state-time-speed"][0]
                sts["eventState"] = 5  # GREEN
                sts["timing"] = {"minEndTime": 10}

    # Publish the emergency SPATEM
    payload = json.dumps(spatem_msg)
    client.publish(SPATEM_MQTT_TOPIC, payload)

# === CAM ===

def publish_cam():
    try:
        cam_msg = load_json(CAM_FILE_PATH)
        
        cam_msg["stationType"] = 15  # Explicitly set RSU type
        cam_msg["latitude"] = 40.6333  # Center of intersection
        cam_msg["longitude"] = -8.6589
        
        cam_msg["generationDeltaTime"] = (int(time.time() * 1000) % 65536)
        
        payload = json.dumps(cam_msg)
        result = client.publish(CAM_MQTT_TOPIC, payload)
        status = result[0]

        if status == 0:
            print(f"Sent CAM message to topic `{CAM_MQTT_TOPIC}`")
        else:
            print(f"Failed to send CAM message to topic `{CAM_MQTT_TOPIC}`")
    except Exception as e:
        print(f"Error publishing CAM message: {str(e)}")


# === MAPEM ===

def publish_mapem():
    mapem_msg = load_json(MAPEM_FILE_PATH)
    payload = json.dumps(mapem_msg)

    result = client.publish(MAPEM_MQTT_TOPIC, payload)
    status = result[0]

    if status == 0:
        print(f"Sent MAPEM message to topic `{MAPEM_MQTT_TOPIC}`")
    else:
        print(f"Failed to send message to topic `{MAPEM_MQTT_TOPIC}`")

# === SPATEM ===

def publish_spatem():
    spatem_msg = load_json(SPATEM_FILE_PATH)
    lights = [0,0,0,0]      # 0 to randomize light value, 3 for red, and 5 for green
    # lights value should be updated based on denm
    spatem_msg = update_spatem(spatem_msg, lights)
    
    payload = json.dumps(spatem_msg)

    result = client.publish(SPATEM_MQTT_TOPIC, payload)
    status = result[0]

    if status == 0:
        print(f"Sent SPATEM message to topic `{SPATEM_MQTT_TOPIC}`")
    else:
        print(f"Failed to send message to topic `{SPATEM_MQTT_TOPIC}`")
        
def update_spatem(spatem_msg, lights):
    global emergency_mode, emergency_mode_expiry, emergency_target_signal
    now = time.time()

    # Emergency override
    if emergency_mode and now < emergency_mode_expiry:
        remaining = int(emergency_mode_expiry - now)
        for intr in spatem_msg["intersections"]:
            for state in intr["states"]:
                # first force RED
                for sts in state["state-time-speed"]:
                    sts["eventState"] = 3
                    sts["timing"] = {"minEndTime": remaining}
                # then if this is the ambulance lane, turn GREEN
                if state.get("signalGroup") == emergency_target_signal:
                    for sts in state["state-time-speed"]:
                        sts["eventState"] = 5
                        sts["timing"] = {"minEndTime": remaining}
        return spatem_msg

    # Emergency expired
    emergency_mode = False
    emergency_target_signal = None

    # Normal 30s cycle
    cycle = (int(now) // 30) % 2
    pattern = ([3,5,3,5] if cycle == 0 else [5,3,5,3])
    for intr in spatem_msg["intersections"]:
        for state in intr["states"]:
            idx = {1:0, 3:1, 5:2, 7:3}.get(state.get("signalGroup"))
            if idx is not None:
                for sts in state["state-time-speed"]:
                    sts["eventState"] = pattern[idx]
                    sts["timing"] = {"minEndTime": 30 - (int(now) % 30)}
    return spatem_msg

# === Main Loop ===
if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            publish_spatem()
            mapem_counter += 1
            if mapem_counter == 10:
                publish_cam()
                publish_mapem()
                mapem_counter = 0
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
