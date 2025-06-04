import json
import time
import copy
import paho.mqtt.client as mqtt
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# === Configuration ===
MQTT_BROKER = "192.168.98.10"
MQTT_PORT = 1883
SPATEM_MQTT_TOPIC = "vanetza/time/spatem"
SPATEM_MQTT_TOPIC2 = "vanetza/in/spatem"
SPATEM_FILE_PATH = "rsu_spatem.json"
MAPEM_MQTT_TOPIC = "vanetza/time/mapem"
MAPEM_FILE_PATH = "rsu_mapem.json"
CAM_MQTT_TOPIC = "vanetza/time/cam"
CAM_FILE_PATH = "rsu_cam.json"
DENM_MQTT_TOPIC = "vanetza/out/denm"
PUBLISH_INTERVAL = 0.6

# === Tracking ===
mapem_counter = 0
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
client = mqtt.Client(client_id=f"rsu_publisher_{int(time.time())}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("RSU Connected to MQTT Broker")
        client.subscribe("vanetza/out/denm")
    else:
        logging.error(f"RSU Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"RSU Disconnected from broker with code {rc}")
    if rc != 0:
        logging.info("RSU Attempting to reconnect...")

def ensure_connection():
    """Ensure MQTT connection is active"""
    if not client.is_connected():
        try:
            logging.info("RSU Reconnecting to MQTT broker...")
            client.reconnect()
            time.sleep(1)  
        except Exception as e:
            logging.error(f"RSU Reconnection failed: {e}")
            return False
    return True

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        if topic == "vanetza/out/denm":
            logging.info("Received DENM message from OBU")
            handle_emergency_denm(payload)
    except Exception as e:
        logging.error(f"Error processing message: {e}")

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, keepalive=15)

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
    emergency_duration = 10 

    spatem_msg = load_json(SPATEM_FILE_PATH)
    
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
        
        cam_msg["stationType"] = 15  
        cam_msg["latitude"] = 40.6333
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
    lights = [0,0,0,0]
    spatem_msg = update_spatem(spatem_msg, lights)
    
    payload = json.dumps(spatem_msg)

    result = client.publish(SPATEM_MQTT_TOPIC, payload)
    status = result[0]

    if status == 0:
        print(f"Sent SPATEM message to topic `{SPATEM_MQTT_TOPIC}`")
    else:
        print(f"Failed to send message to topic `{SPATEM_MQTT_TOPIC}`")
        
    result2 = client.publish(SPATEM_MQTT_TOPIC2, payload)
    status2 = result2[0]
    
    if status2 == 0:
        print(f"Sent SPATEM message to topic `{SPATEM_MQTT_TOPIC2}`")
    else:
        print(f"Failed to send message to topic `{SPATEM_MQTT_TOPIC2}`")
        
def update_spatem(spatem_msg, lights):
    global emergency_mode, emergency_mode_expiry, emergency_target_signal
    now = time.time()

    if emergency_mode and now < emergency_mode_expiry:
        remaining = int(emergency_mode_expiry - now)
        for intr in spatem_msg["intersections"]:
            for state in intr["states"]:
                for sts in state["state-time-speed"]:
                    sts["eventState"] = 3
                    sts["timing"] = {"minEndTime": remaining}
                if state.get("signalGroup") == emergency_target_signal:
                    for sts in state["state-time-speed"]:
                        sts["eventState"] = 5
                        sts["timing"] = {"minEndTime": remaining}
        return spatem_msg

    emergency_mode = False
    emergency_target_signal = None

    cycle = (int(now) // 10) % 2
    pattern = ([3,5,3,5] if cycle == 0 else [5,3,5,3])
    for intr in spatem_msg["intersections"]:
        for state in intr["states"]:
            idx = {1:0, 3:1, 5:2, 7:3}.get(state.get("signalGroup"))
            if idx is not None:
                for sts in state["state-time-speed"]:
                    sts["eventState"] = pattern[idx]
                    sts["timing"] = {"minEndTime": 10 - (int(now) % 10)}
    return spatem_msg

# === Main Loop ===
if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            if ensure_connection():
                publish_spatem()
                mapem_counter += 1
                if mapem_counter == 1:
                    publish_cam()
                    publish_mapem()
                    mapem_counter = 0
            else:
                logging.warning("RSU Not connected, skipping publish cycle")
                time.sleep(1)
                
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        logging.info("RSU Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
