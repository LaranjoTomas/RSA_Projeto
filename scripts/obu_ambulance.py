import json
import time
import paho.mqtt.client as mqtt

# === Configuration ===
MQTT_BROKER = "192.168.98.20"
MQTT_PORT = 1883
MQTT_TOPIC = "vanetza/in/cam"
JSON_FILE_PATH = "rsu_mapem.json"
PUBLISH_INTERVAL = 5  # seconds

# === Load MAPEM JSON ===
def load_mapem_message(filepath):
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

# === Main Loop ===
def publish_mapem():
    mapem_msg = load_mapem_message(JSON_FILE_PATH)
    payload = json.dumps(mapem_msg)

    while True:
        result = client.publish(MQTT_TOPIC, payload)
        status = result[0]

        if status == 0:
            print(f"Sent MAPEM message to topic `{MQTT_TOPIC}`")
        else:
            print(f"Failed to send message to topic `{MQTT_TOPIC}`")

        time.sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    client.loop_start()
    try:
        publish_mapem()
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        client.loop_stop()
        client.disconnect()
