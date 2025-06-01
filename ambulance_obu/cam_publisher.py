import json
import paho.mqtt.client as mqtt
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for dynamic coordinates (starting near the intersection)
current_lat = 40.6329
current_lng = -8.6585
# Step for latitude update; keeps movement small so the vehicle remains on the map.
lat_step = 0.00010

def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code " + str(rc))
    # client.subscribe("vanetza/out/#")

def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    logger.info(f"Topic: {msg.topic}")
    logger.info(f"Message: {message}")

def update_coordinates():
    global current_lat, lat_step
    # Update latitude by a small step; reverse direction on reaching boundaries
    current_lat += lat_step
    # Boundaries: oscillate between 40.6325 and 40.6335
    if current_lat > 40.6335 or current_lat < 40.6325:
        lat_step = -lat_step
        current_lat += lat_step  # update once more after reversing
    return current_lat, current_lng

def generate_cam():
    try:
        # Load sample CAM message from file
        with open('../vanetza-nap-master/examples/in_cam.json') as f:
            cam_message = json.load(f)
        
        # Update coordinates dynamically
        lat, lng = update_coordinates()
        cam_message["latitude"] = lat
        cam_message["longitude"] = lng
        
        # Generate current timestamp (CAM field)
        cam_message["generationDeltaTime"] = (int(time.time() * 1000) % 65536)
        
        # Convert to JSON and publish
        message_json = json.dumps(cam_message)
        client.publish("vanetza/in/cam", message_json)
        
        # Log the full CAM message as well as a summary
        logger.info(f"Full CAM message: {message_json}")
        logger.info(f"Published CAM message: lat={lat:.7f}, lng={lng:.7f}")
        
    except Exception as e:
        logger.error(f"Error generating CAM: {e}")

# Initialize MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect("192.168.98.20", 1883, 60)
    
    # Start network loop in background thread
    client.loop_start()
    
    # Main loop for sending CAM messages
    while True:
        generate_cam()
        time.sleep(2)
        
except KeyboardInterrupt:
    logger.info("Script terminated by user")
except Exception as e:
    logger.error(f"Error: {e}")
finally:
    client.loop_stop()
    client.disconnect()