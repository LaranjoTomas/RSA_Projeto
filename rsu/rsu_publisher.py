import json
import time
import random
import paho.mqtt.client as mqtt

# === Configuration ===
MQTT_BROKER = "192.168.98.10"
MQTT_PORT = 1883
SPATEM_MQTT_TOPIC = "vanetza/in/spatem"
SPATEM_FILE_PATH = "rsu_spatem.json"
MAPEM_MQTT_TOPIC = "vanetza/in/mapem"
MAPEM_FILE_PATH = "rsu_mapem.json"
PUBLISH_INTERVAL = 0.1  # seconds

# === Tracking ===
mapem_counter = 0   # publish mapem every 10 cam/spatem -> 1 Hz
lights = [0,0,0,0]

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
        
def update_spatem(spatem_msg,lights):
    for i in range(len(lights)):
        lights[i] = random.choice([3, 5])
            
    for intersection in spatem_msg['intersections']:
        for state in intersection['states']:
            if state['signalGroup'] == 1:
                state['state-time-speed']['eventState'] = lights[0]
            if state['signalGroup'] == 3:
                state['state-time-speed']['eventState'] = lights[1]
            if state['signalGroup'] == 5:
                state['state-time-speed']['eventState'] = lights[2]
            if state['signalGroup'] == 7:
                state['state-time-speed']['eventState'] = lights[3]
    return spatem_msg

# === Main Loop ===
if __name__ == "__main__":
    client.loop_start()
    try:
        while True:
            publish_spatem()
            mapem_counter += 1
            if mapem_counter == 10:
                publish_mapem
                mapem_counter = 0
            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
