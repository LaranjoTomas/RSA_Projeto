from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import time
import json
import math
import threading
import logging
import requests
import paho.mqtt.client as mqtt

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='app/build', static_url_path='')
CORS(app)

INTERSECTION_RADIUS = 15  # meters
LANE_WIDTH = 2.0 # meters

vanetza_messages = {
    'cam': [],
    'denm': [],
    'spatem': [],
    'mapem': [],
    'cpm': [],
    'vam': []
}

last_spatem_update = 0

rsu_position = { 
    'lat': 40.6329,
    'lng': -8.6585
}

def setup_mqtt_client():
    client = mqtt.Client(client_id=f"rsu_server_1")
    
    def on_connect(client, userdata, flags, rc):
        logger.info("Connected to MQTT broker with result code " + str(rc))
        # Subscribe to all Vanetza topics
        client.subscribe("vanetza/out/cam") # To receive OBU CAM messages
        client.subscribe("vanetza/time/spatem") # To receive RSU SPATEM messages, for the semaphore state
        client.subscribe("vanetza/time/cam") # If needed, to receive RSU CAM messages

    def on_message(client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic == "vanetza/time/spatem":
                logger.info(f"Received SPATEM message on {topic}")
                print(f"SPATEM MESSAGE: {json.dumps(payload, indent=2)}")
                if 'spatem' in vanetza_messages:
                    vanetza_messages['spatem'].append(payload)
                    if len(vanetza_messages['spatem']) > 100:
                        vanetza_messages['spatem'].pop(0)
                handle_spatem_message(payload)
                
            elif topic == "vanetza/time/cam":
                logger.info(f"Received CAM message on {topic}")
                logger.info(f"CAM message type: {payload.get('stationType')}")
                # Check for emergency vehicle (ambulance)
                if payload.get("stationType") == 10:
                    logger.info("Processing emergency CAM message from ambulance")
                    handle_ambulance_cam(payload)
                elif payload.get("stationType") == 15:  # RSU station type
                    logger.info(f"Processing RSU CAM: {json.dumps(payload, indent=2)}")
                    handle_rsu_cam_message(payload)
                elif payload.get("stationType") == 5:  # Regular vehicle
                    logger.info("Processing regular vehicle CAM message")
                    handle_cam_message(payload)
                else:
                    logger.info("Processing regular CAM message")
                    handle_cam_message(payload)
            
            # Handle input CAM messages specifically
            elif topic == "vanetza/out/cam":
                logger.info(f"Received CAM message on {topic}")
                station_type = payload.get("stationType", 0)
                if station_type == 10:  # Emergency vehicle (ambulance)
                    logger.info("Processing emergency CAM message from ambulance")
                    handle_ambulance_cam(payload)
                elif station_type == 5:  # Normal vehicle
                    logger.info("Processing normal vehicle CAM message")
                    handle_cam_message(payload)
                else:
                    handle_cam_message(payload)
                
            # Continue handling output messages as before
            elif "out" in topic:
                message_type = topic.split('/')[-1]
                if message_type in vanetza_messages:
                    max_msgs = 100
                    vanetza_messages[message_type].append(payload)
                    if len(vanetza_messages[message_type]) > max_msgs:
                        vanetza_messages[message_type].pop(0)
                    logger.info(f"Received output {message_type} message")
                    
        except Exception as e:
            logger.error(f"Error processing MQTT message: {str(e)}")
            logger.error(f"Message payload: {msg.payload.decode()}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        logger.info("Trying to connect to MQTT broker at 192.168.98.10...")
        client.connect("192.168.98.10", 1883, 60)
        
        mqtt_thread = threading.Thread(target=client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        logger.info("MQTT client started successfully using Docker network")
    except Exception as e:
        logger.error(f"Failed to connect to Docker MQTT broker: {str(e)}")
        try:
            logger.info("Trying to connect to local MQTT broker...")
            client.connect("127.0.0.1", 1883, 60)
            
            mqtt_thread = threading.Thread(target=client.loop_forever)
            mqtt_thread.daemon = True
            mqtt_thread.start()
            logger.info("MQTT client started successfully with local connection")
        except Exception as e2:
            logger.error(f"Failed to connect to any MQTT broker: {str(e2)}")

def handle_spatem_message(spatem_payload):
    """Process incoming SPATEM messages and update traffic light states"""
    try:
        global last_spatem_update
        logger.info("Processing SPATEM message to update traffic lights")
        logger.info(f"SPATEM keys: {list(spatem_payload.keys())}")
        
        last_spatem_update = int(time.time())

        if "fields" in spatem_payload and "spatem" in spatem_payload["fields"]:
            spatem_data = spatem_payload["fields"]["spatem"]
        elif "intersections" in spatem_payload:
            spatem_data = spatem_payload  
        else:
            logger.warning("SPATEM message does not contain expected fields")
            return
        
        # Extract intersection data
        if "intersections" not in spatem_data:
            logger.warning("No intersections found in SPATEM message")
            return
            
        # Map signalGroup to traffic light direction
        signal_group_to_direction = {
            1: "NORTH",
            3: "EAST", 
            5: "SOUTH",
            7: "WEST"
        }
        
        # Event state mapping (3 is RED, 5 is GREEN)
        event_state_to_color = {
            3: "RED",
            5: "GREEN"
        }
        
        for intersection in spatem_data["intersections"]:
            for state in intersection.get("states", []):
                signal_group = state.get("signalGroup")
                direction = signal_group_to_direction.get(signal_group)
                
                if direction:
                    for sts in state.get("state-time-speed", []):
                        event_state = sts.get("eventState")
                        if event_state in event_state_to_color:
                            color = event_state_to_color[event_state]
                            
                            # Update the corresponding traffic light
                            for light in traffic_data['traffic_lights']:
                                if light['direction'] == direction:
                                    light['state'] = color
                                    light['countdown'] = sts.get("timing", {}).get("minEndTime", 30) % 100
                                    logger.info(f"Updated traffic light {light['id']} to {color}")
                                    break
    
    except Exception as e:
        logger.error(f"Error processing SPATEM message: {str(e)}", exc_info=True)

def handle_rsu_cam_message(cam_payload):
    """Process incoming CAM messages from RSU and update RSU position"""
    try:
        global rsu_position
        
        # Extract station info to confirm it's from an RSU
        station_id = cam_payload.get("stationID", 0)
        station_type = cam_payload.get("stationType", 0)
        
        if station_type == 15:  # RSU type
            # Extract position
            if "fields" in cam_payload and "cam" in cam_payload["fields"]:
                cam_data = cam_payload["fields"]["cam"]
            else:
                cam_data = cam_payload
            
            latitude = cam_data.get("latitude")
            longitude = cam_data.get("longitude")
            
            if latitude is not None and longitude is not None:
                # Update the RSU position
                rsu_position['lat'] = latitude
                rsu_position['lng'] = longitude
                logger.info(f"Updated RSU position: ID={station_id}, lat={latitude}, lng={longitude}")
                
                # Add RSU to traffic_data if not already present
                rsu = next((item for item in traffic_data.get('rsu_nodes', []) if item['id'] == f'rsu_{station_id}'), None)
                
                if rsu:
                    rsu['position'] = {'lat': latitude, 'lng': longitude}
                else:
                    if 'rsu_nodes' not in traffic_data:
                        traffic_data['rsu_nodes'] = []
                        
                    traffic_data['rsu_nodes'].append({
                        'id': f'rsu_{station_id}',
                        'type': 'rsu',
                        'position': {'lat': latitude, 'lng': longitude},
                    })
    
    except Exception as e:
        logger.error(f"Error processing RSU CAM message: {str(e)}", exc_info=True)

def handle_ambulance_cam(cam_message):
    """Process incoming CAM messages from emergency (ambulance) vehicles."""
    try:
        # Extract identifying and position info
        station_id = str(cam_message.get("stationID", "unknown"))
        latitude = cam_message.get("latitude")
        longitude = cam_message.get("longitude")
        heading = cam_message.get("heading", 0)
        speed = cam_message.get("speed", 0)
        
        if latitude is None or longitude is None:
            logger.warning("Ambulance CAM message missing coordinates")
            return
        
        # Try to update an existing ambulance vehicle
        vehicle = next((v for v in traffic_data['vehicles']
                        if v.get('station_id') == station_id and v.get('type') == 'ambulance'), None)
        
        if vehicle:
            vehicle['position'] = {'lat': latitude, 'lng': longitude}
            vehicle['heading'] = heading
            vehicle['speed'] = speed
            vehicle['emergency'] = True
            logger.info(f"Updated ambulance vehicle: ID={station_id}")
        else:
            new_vehicle = {
                'id': f'v_ambulance_{len(traffic_data["vehicles"]) + 1}',
                'station_id': station_id,
                'type': 'ambulance',
                'position': {'lat': latitude, 'lng': longitude},
                'heading': heading,
                'speed': speed,
                'emergency': True,
                'waiting': False
            }
            traffic_data['vehicles'].append(new_vehicle)
            logger.info(f"Added new ambulance vehicle: ID={station_id}")
    except Exception as e:
        logger.error(f"Error handling ambulance CAM message: {str(e)}", exc_info=True)

def handle_cam_message(cam_message):
    """Process incoming CAM messages and update vehicle positions"""
    try:
        # Extract station ID to identify the vehicle
        station_id = str(cam_message.get("stationID", "unknown"))
        
        # Log the full message for debugging
        logger.info(f"Processing CAM message: {station_id}")
        logger.debug(f"CAM message content: {cam_message}")
        
        # Extract GPS coordinates from CAM message
        latitude = cam_message.get("latitude")
        longitude = cam_message.get("longitude")
        heading = cam_message.get("heading")
        speed = cam_message.get("speed")
        
        if latitude is None or longitude is None:
            logger.warning(f"CAM message missing coordinates: {cam_message}")
            return
            
        if heading == 3601:
            heading = 0
        elif heading is not None:
            heading = float(heading)
            
        if speed == 16383:
            speed = 0
        elif speed is not None:
            speed = float(speed)
        else:
            speed = 50  # Default value

        vehicle = next((v for v in traffic_data['vehicles'] if v.get('station_id') == station_id), None)
        
        if vehicle:
            # Update existing vehicle
            vehicle['position'] = {
                'lat': latitude,
                'lng': longitude
            }
            if heading is not None:
                vehicle['heading'] = heading
            if speed is not None:
                vehicle['speed'] = speed
                
            logger.info(f"Updated vehicle position: ID={station_id}, lat={latitude}, lng={longitude}")
        else:
            new_vehicle = {
                'id': f'v_cam_{len(traffic_data["vehicles"]) + 1}',
                'station_id': station_id,
                'type': 'car',  # Default type
                'position': {'lat': latitude, 'lng': longitude},
                'heading': heading if heading is not None else 0,
                'speed': speed if speed is not None else 50,
                'waiting': False,
                'cam_source': True  # Flag to identify CAM-sourced vehicles
            }
            
            vehicle_type = cam_message.get("stationType", 0)
            if vehicle_type == 10:
                new_vehicle['type'] = 'ambulance'
                
            # Add vehicle to the list
            traffic_data['vehicles'].append(new_vehicle)
            logger.info(f"Added new vehicle from CAM: ID={station_id}, lat={latitude}, lng={longitude}")
            
    except Exception as e:
        logger.error(f"Error handling CAM message: {str(e)}", exc_info=True)

# Convert GPS coordinates to meters
def gps_to_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi/2) * math.sin(delta_phi/2) + 
         math.cos(phi1) * math.cos(phi2) * 
         math.sin(delta_lambda/2) * math.sin(delta_lambda/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def local_to_gps(x, y, center_lat, center_lng):
    R = 6371000
    
    # Calculate latitude change
    lat_change = (y / R) * (180 / math.pi)
    # Calculate longitude change (accounting for latitude)
    lng_change = (x / R) * (180 / math.pi) / math.cos(math.radians(center_lat))
    
    return {
        'lat': center_lat + lat_change,
        'lng': center_lng + lng_change
    }

def gps_to_local(lat, lng, center_lat, center_lng):
    R = 6371000
    # Calculate x (longitude) change
    x = math.cos(math.radians(center_lat)) * R * math.radians(lng - center_lng)
    # Calculate y (latitude) change 
    y = R * math.radians(lat - center_lat)
    
    return (x, y)

# Traffic light states
traffic_data = {
    'intersection_id': 'intersection_1',
    'timestamp': 0,
    'center': {'lat': 40.6329, 'lng': -8.6585},
    'traffic_lights': [
        {
            'id': 'tl_1',
            'position': {'lat': 40.6331, 'lng': -8.6585},
            'state': 'RED',
            'direction': 'NORTH',
            'countdown': 30
        },
        {
            'id': 'tl_2',
            'position': {'lat': 40.6329, 'lng': -8.6583},
            'state': 'GREEN',
            'direction': 'EAST',
            'countdown': 20
        },
        {
            'id': 'tl_3',
            'position': {'lat': 40.6327, 'lng': -8.6585},
            'state': 'RED',
            'direction': 'SOUTH',
            'countdown': 30
        },
        {
            'id': 'tl_4',
            'position': {'lat': 40.6329, 'lng': -8.6587},
            'state': 'GREEN',
            'direction': 'WEST',
            'countdown': 20
        }
    ],
    'vehicles': [
        # {
        #     'id': 'v_1',
        #     'type': 'car',
        #     'position': {'lat': 40.6360, 'lng': -8.6586}, 
        #     'heading': 180,  # Heading in degrees (0=North, 90=East, 180=South, 270=West)
        #     'speed': 80,
        #     'waiting': False
        # },
        # {
        #     'id': 'v_2',
        #     'type': 'ambulance',
        #     'position': {'lat': 40.6325, 'lng': -8.6550}, 
        #     'heading': 270,  # Heading west
        #     'speed': 90,
        #     'emergency': True,
        #     'denm_sent': False,
        #     'waiting': False
        # }
    ],
    'rsu_nodes': [],
    'emergency_mode': False,
    'emergency_vehicle': None
}

# Road network model
road_network = {
    'intersection': {
        'center': {'x': 0, 'y': 0},  # Local coordinates (0,0)
        'radius': INTERSECTION_RADIUS
    },
    'lanes': {
        'north': {
            'start': {'x': 0, 'y': -50},  # 50m south of center
            'end': {'x': 0, 'y': 50},     # 50m north of center
            'width': LANE_WIDTH,
            'direction': 0  # Degrees (North)
        },
        'east': {
            'start': {'x': -50, 'y': 0},  # 50m west of center
            'end': {'x': 50, 'y': 0},     # 50m east of center
            'width': LANE_WIDTH,
            'direction': 90  # Degrees (East)
        },
        'south': {
            'start': {'x': 0, 'y': 50},   # 50m north of center
            'end': {'x': 0, 'y': -50},    # 50m south of center
            'width': LANE_WIDTH,
            'direction': 180  # Degrees (South)
        },
        'west': {
            'start': {'x': 50, 'y': 0},   # 50m east of center
            'end': {'x': -50, 'y': 0},    # 50m west of center
            'width': LANE_WIDTH,
            'direction': 270  # Degrees (West)
        }
    }
}

# Normal traffic light cycle
def update_normal_traffic_lights(current_time):
    cycle = (current_time // 30) % 2
    if cycle == 0:
        traffic_data['traffic_lights'][0]['state'] = 'RED'    # North
        traffic_data['traffic_lights'][1]['state'] = 'GREEN'  # West
        traffic_data['traffic_lights'][2]['state'] = 'RED'    # North
        traffic_data['traffic_lights'][3]['state'] = 'GREEN'  # East
    else:
        traffic_data['traffic_lights'][0]['state'] = 'GREEN'  # North
        traffic_data['traffic_lights'][1]['state'] = 'RED'    # Wast
        traffic_data['traffic_lights'][2]['state'] = 'GREEN'  # South
        traffic_data['traffic_lights'][3]['state'] = 'RED'    # East
    
    # Update countdowns
    for light in traffic_data['traffic_lights']:
        light['countdown'] = 30 - (current_time % 30)

# Emergency mode traffic light control
def handle_emergency_vehicle():
    # First, set all lights to red
    for light in traffic_data['traffic_lights']:
        light['state'] = 'RED'
        light['countdown'] = 30
    
    # Determine which direction the emergency vehicle is heading
    emergency_vehicle = traffic_data['emergency_vehicle']
    if not emergency_vehicle:
        return
    
    heading = emergency_vehicle['heading']
    
    # Set the appropriate light to green based on heading
    if 315 <= heading or heading < 45:  # Heading North
        for light in traffic_data['traffic_lights']:
            if light['direction'] == 'NORTH':
                light['state'] = 'GREEN'
                break
    elif 45 <= heading < 135:  # Heading East
        for light in traffic_data['traffic_lights']:
            if light['direction'] == 'EAST':
                light['state'] = 'GREEN'
                break
    elif 135 <= heading < 225:  # Heading South
        for light in traffic_data['traffic_lights']:
            if light['direction'] == 'SOUTH':
                light['state'] = 'GREEN'
                break
    elif 225 <= heading < 315:  # Heading West
        for light in traffic_data['traffic_lights']:
            if light['direction'] == 'WEST':
                light['state'] = 'GREEN'
                break

# Determine if a vehicle is close to the intersection
def is_vehicle_near_intersection(vehicle, center, radius=50):
    vehicle_pos = vehicle['position']
    center_pos = center
    
    # Calculate distance between vehicle and intersection center
    distance = gps_to_meters(
        vehicle_pos['lat'], vehicle_pos['lng'],
        center_pos['lat'], center_pos['lng']
    )
    
    return distance < radius

# Get the traffic light for a given direction
def get_traffic_light(direction):
    for light in traffic_data['traffic_lights']:
        if light['direction'] == direction:
            return light
    return None

# Send DENM message (simulate communication with vanetza)
def send_denm_message(vehicle):
    try:
        # Prepare DENM message
        denm_message = {
            "management": {
                "actionID": {
                    "originatingStationID": vehicle['id'],
                    "sequenceNumber": 1
                },
                "detectionTime": int(time.time()),
                "referenceTime": int(time.time()),
                "eventPosition": {
                    "latitude": vehicle['position']['lat'] * 10000000,
                    "longitude": vehicle['position']['lng'] * 10000000
                }
            },
            "situation": {
                "eventType": {
                    "causeCode": 6,  # Emergency vehicle approaching
                    "subCauseCode": 1
                }
            },
            "location": {
                "eventPosition": {
                    "latitude": vehicle['position']['lat'] * 10000000,
                    "longitude": vehicle['position']['lng'] * 10000000
                },
                "eventPositionHeading": vehicle['heading']
            }
        }
        
        # Log the DENM message
        logger.info(f"Sending DENM message for vehicle {vehicle['id']}")
        
        response = requests.post(
            "http://localhost:3000/api/denm", 
            json=denm_message, 
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"DENM response: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Error sending DENM message: {str(e)}")
        return False

@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/traffic', methods=['GET'])
def get_traffic_data():
    # Simulate movement and state changes
    current_time = int(time.time())
    traffic_data['timestamp'] = current_time
    
    # Check if any emergency vehicles with emergency mode are near the intersection
    for vehicle in traffic_data['vehicles']:
        if 'station_id' not in vehicle:
            vehicle['station_id'] = vehicle['id']
        if vehicle['type'] == 'ambulance' and vehicle.get('emergency', False):
            # Check if vehicle is approaching intersection and DENM hasn't been sent
            if is_vehicle_near_intersection(vehicle, traffic_data['center'], 80) and not vehicle.get('denm_sent', False):
                # Send DENM message when approaching intersection
                vehicle['denm_sent'] = True
                send_denm_message(vehicle)
                
            # If very close to intersection, activate emergency mode
            if is_vehicle_near_intersection(vehicle, traffic_data['center']):
                if not traffic_data['emergency_mode']:
                    logger.info(f"Emergency vehicle {vehicle['id']} detected near intersection")
                traffic_data['emergency_mode'] = True
                traffic_data['emergency_vehicle'] = vehicle
                break
    else:
        # No emergency vehicles found, reset to normal mode
        if traffic_data['emergency_mode']:
            logger.info("No emergency vehicles near intersection, returning to normal mode")
            # Reset DENM sent flag for all emergency vehicles
            for vehicle in traffic_data['vehicles']:
                if vehicle['type'] == 'ambulance':
                    vehicle['denm_sent'] = False
                    
        traffic_data['emergency_mode'] = False
        traffic_data['emergency_vehicle'] = None
    
    # Update traffic lights
    if traffic_data['emergency_mode']:
        handle_emergency_vehicle()
    
    update_vehicle_positions()
    
    return jsonify(traffic_data)

@app.route('/api/emergency', methods=['POST'])
def trigger_emergency():
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    action = data.get('action', 'activate')
    
    vehicle = next((v for v in traffic_data['vehicles'] if v['id'] == vehicle_id), None)
    if not vehicle:
        return jsonify({'status': 'error', 'message': f'Vehicle {vehicle_id} not found'}), 404
    
    if action == 'activate':
        vehicle['emergency'] = True
        message = f'Emergency mode activated for vehicle {vehicle_id}'
    else:
        vehicle['emergency'] = False
        message = f'Emergency mode deactivated for vehicle {vehicle_id}'
    
    return jsonify({'status': 'success', 'message': message})

@app.route('/api/denm', methods=['POST'])
def receive_denm():
    """
    Endpoint to receive DENM messages from Vanetza OBU
    """
    try:
        data = request.get_json()
        logger.info(f"Received DENM message: {data}")
        
        # Check if this is an emergency vehicle DENM
        if 'management' in data and 'actionID' in data['management']:
            action_id = data['management']['actionID']
            
            # Extract vehicle ID from actionID if available
            vehicle_id = action_id.get('originatingStationID', None)
            
            # Check if there's an emergency event
            if 'situation' in data and 'eventType' in data['situation']:
                event_type = data['situation']['eventType']
                
                # Check for emergency vehicle approaching event
                if (event_type.get('causeCode') == 6 and 
                    event_type.get('subCauseCode') in [1, 2]):  # Emergency vehicle approaching
                    
                    # Extract position if available
                    if 'location' in data and 'eventPosition' in data['location']:
                        position = data['location']['eventPosition']
                        lat = position.get('latitude', 0) / 10000000  # Convert from decidegree
                        lng = position.get('longitude', 0) / 10000000
                        
                        # Find or create the emergency vehicle
                        vehicle = next((v for v in traffic_data['vehicles'] if str(v['id']) == str(vehicle_id)), None)
                        
                        if vehicle:
                            # Update existing vehicle
                            vehicle['position'] = {'lat': lat, 'lng': lng}
                            vehicle['emergency'] = True
                            vehicle['denm_sent'] = True
                        else:
                            # Create new emergency vehicle
                            new_vehicle = {
                                'id': f'v_{len(traffic_data["vehicles"]) + 1}',
                                'vanetza_id': vehicle_id,
                                'type': 'ambulance',
                                'position': {'lat': lat, 'lng': lng},
                                'heading': data['location'].get('eventPositionHeading', 0),
                                'speed': 40,
                                'emergency': True,
                                'denm_sent': True
                            }
                            traffic_data['vehicles'].append(new_vehicle)
                        
                        return jsonify({
                            'status': 'success', 
                            'message': 'DENM processed, emergency vehicle detected'
                        })
        
        return jsonify({
            'status': 'success', 
            'message': 'DENM received but not an emergency vehicle notification'
        })
        
    except Exception as e:
        logger.error(f"Error processing DENM message: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/vehicle/change-direction', methods=['POST'])
def change_vehicle_direction():
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    new_heading = data.get('heading')
    
    if not vehicle_id or new_heading is None:
        return jsonify({'status': 'error', 'message': 'Missing vehicle_id or heading'}), 400
    
    vehicle = next((v for v in traffic_data['vehicles'] if v['id'] == vehicle_id), None)
    if not vehicle:
        return jsonify({'status': 'error', 'message': f'Vehicle {vehicle_id} not found'}), 404
    
    # Update vehicle heading and adjust position for right side of road
    vehicle['heading'] = new_heading
    
    # Reset position to be on the right side of the road
    center = traffic_data['center']
    offset = 0.0001
    
    if new_heading == 0:  # Northbound - right side is east
        vehicle['position'] = {'lat': center['lat'] - 0.006, 'lng': center['lng'] + offset}
    elif new_heading == 90:  # Eastbound - right side is south
        vehicle['position'] = {'lat': center['lat'] - offset, 'lng': center['lng'] - 0.006}
    elif new_heading == 180:  # Southbound - right side is west
        vehicle['position'] = {'lat': center['lat'] + 0.006, 'lng': center['lng'] - offset}
    elif new_heading == 270:  # Westbound - right side is north
        vehicle['position'] = {'lat': center['lat'] + offset, 'lng': center['lng'] + 0.006}
    
    return jsonify({
        'status': 'success', 
        'message': f'Vehicle {vehicle_id} now heading {new_heading} degrees'
    })

def update_vehicle_positions():
    """Update vehicle positions to move through the intersection"""
    center = traffic_data['center']
    
    for vehicle in traffic_data['vehicles']:
        # Update position based on heading
        if vehicle.get('cam_source', False):
            # Don't update these vehicles' positions, they're controlled by CAM messages
            continue
        local_pos = gps_to_local(vehicle['position']['lat'], vehicle['position']['lng'], center['lat'], center['lng'])

        heading = vehicle['heading']
        
        # Get the traffic light for this direction
        direction_map = {0: 'NORTH', 90: 'EAST', 180: 'SOUTH', 270: 'WEST'}
        direction = direction_map.get(heading)
        light = get_traffic_light(direction)
        
        # Check if vehicle should stop at red light
        if (light and light['state'] == 'RED' and not vehicle.get('emergency', False) and
            is_vehicle_near_intersection(vehicle, center, 40) and
            not is_vehicle_near_intersection(vehicle, center, 15)):
            vehicle['waiting'] = True
            continue
        else:
            vehicle['waiting'] = False
            
        if vehicle['waiting']:
            continue
            
        # Calculate speed factor based on vehicle speed
        speed_factor = 0.000065 * vehicle['speed'] / 30  # Scale factor for speed
        
        lane_offset = 0.0001
        
        if heading == 0:  # Northbound
            # Move vehicle north
            vehicle['position']['lat'] += speed_factor
            
            # Keep on right side (east side of north road)
            vehicle['position']['lng'] = center['lng'] + lane_offset
            
            # If passed north edge, reset to south
            if vehicle['position']['lat'] > center['lat'] + 0.008:
                vehicle['position']['lat'] = center['lat'] - 0.008
                
        elif heading == 90:  # Eastbound
            # Move vehicle east
            vehicle['position']['lng'] += speed_factor
            
            # Keep on right side (south side of east road)
            vehicle['position']['lat'] = center['lat'] - lane_offset
            
            # If passed east edge, reset to west
            if vehicle['position']['lng'] > center['lng'] + 0.008:
                vehicle['position']['lng'] = center['lng'] - 0.008
                
        elif heading == 180:  # Southbound
            # Move vehicle south
            vehicle['position']['lat'] -= speed_factor
            
            # Keep on right side (west side of south road)
            vehicle['position']['lng'] = center['lng'] - lane_offset
            
            # If passed south edge, reset to north
            if vehicle['position']['lat'] < center['lat'] - 0.008:
                vehicle['position']['lat'] = center['lat'] + 0.008
                
        elif heading == 270:  # Westbound
            # Move vehicle west
            vehicle['position']['lng'] -= speed_factor
            
            # Keep on right side (north side of west road)
            vehicle['position']['lat'] = center['lat'] + lane_offset
            
            # If passed west edge, reset to east
            if vehicle['position']['lng'] < center['lng'] - 0.008:
                vehicle['position']['lng'] = center['lng'] + 0.008

@app.route('/api/config', methods=['GET'])
def get_config():
    config = {
        'map_center': traffic_data['center'],
        'zoom': 17,  # Reduced zoom
        'update_interval': 1000,  # ms
        'simulation_speed': 1,
        'directions': {
            'north': 0,
            'east': 90,
            'south': 180,
            'west': 270
        }
    }
    return jsonify(config)

@app.route('/api/road_network', methods=['GET'])
def get_road_network():
    """Return the road network model with GPS coordinates"""
    center_gps = traffic_data['center']
    
    # Convert local road network to GPS coordinates
    gps_road_network = {
        'intersection': {
            'center': center_gps,
            'radius': INTERSECTION_RADIUS
        },
        'lanes': {}
    }
    
    for name, lane in road_network['lanes'].items():
        start_gps = local_to_gps(lane['start']['x'], lane['start']['y'], 
                               center_gps['lat'], center_gps['lng'])
        end_gps = local_to_gps(lane['end']['x'], lane['end']['y'], 
                             center_gps['lat'], center_gps['lng'])
        
        gps_road_network['lanes'][name] = {
            'start': start_gps,
            'end': end_gps,
            'width': lane['width'],
            'direction': lane['direction']
        }
    
    return jsonify(gps_road_network)

@app.route('/api/vanetza_messages', methods=['GET'])
def get_vanetza_messages():
    message_type = request.args.get('type', 'all')
    
    if message_type == 'all':
        return jsonify(vanetza_messages)
    elif message_type in vanetza_messages:
        return jsonify({message_type: vanetza_messages[message_type]})
    else:
        return jsonify({'error': f'Unknown message type: {message_type}'}), 400


if __name__ == '__main__':
    print("====================== RSU Server 1 ======================")
    setup_mqtt_client()
    app.run(host='0.0.0.0', port=3000, debug=True)