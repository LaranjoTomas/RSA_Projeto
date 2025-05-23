import json
import time
import paho.mqtt.client as mqtt

# === Configuration ===
MQTT_BROKER = "192.168.98.20"
MQTT_PORT = 1883
CAM_MQTT_TOPIC = "vanetza/in/cam"
CAM_FILE_PATH = "in_cam.json"
DENM_MQTT_TOPIC = "vanetza/in/denm"
DENM_FILE_PATH = "obu_denm.json"
LANE_FILE_PATH = "lane_coordinates_with_n.json"
PUBLISH_INTERVAL = 0.1  # seconds


# === Tracking ===
denm_counter = 0
current_lane = 1
lane_point = 0

# === Load CAM JSON ===
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

# === CAM ===

def publish_cam():
    cam_msg = load_json(CAM_FILE_PATH)
    
    # add here update to cam based on position
    
    payload = json.dumps(cam_msg)

    result = client.publish(CAM_MQTT_TOPIC, payload)
    status = result[0]

    if status == 0:
        print(f"Sent cam message to topic `{CAM_MQTT_TOPIC}`")
    else:
        print(f"Failed to send message to topic `{CAM_MQTT_TOPIC}`")
        
# === DENM ===

def publish_denm():
    denm_msg = load_json(DENM_FILE_PATH)
    
    payload = json.dumps(denm_msg)

    result = client.publish(DENM_MQTT_TOPIC, payload)
    status = result[0]

    if status == 0:
        print(f"Sent denm message to topic `{DENM_MQTT_TOPIC}`")
    else:
        print(f"Failed to send message to topic `{DENM_MQTT_TOPIC}`")
    

# === Main Loop ===        

if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            publish_cam()
            denm_counter += 1
            if denm_counter == 10:
                publish_denm()
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
