from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import random
import time
import os
import json
import math
import threading
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='app/build', static_url_path='')
CORS(app)

# Intersection configuration
INTERSECTION_RADIUS = 15  # meters
LANE_WIDTH = 3.5  # meters

# Convert GPS coordinates to meters (rough approximation for small areas)
def gps_to_meters(lat1, lng1, lat2, lng2):
    R = 6371000  # Earth radius in meters
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(dlng/2) * math.sin(dlng/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

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
        {
            'id': 'v_1',
            'type': 'car',
            'position': {'lat': 40.6335, 'lng': -8.6586}, # Offset to right side of road
            'heading': 180,  # Heading in degrees (0=North, 90=East, 180=South, 270=West)
            'speed': 30,
            'waiting': False
        },
        {
            'id': 'v_2',
            'type': 'ambulance',
            'position': {'lat': 40.6325, 'lng': -8.6579}, # Offset to right side of road
            'heading': 270,  # Heading west
            'speed': 40,
            'emergency': False,
            'denm_sent': False,
            'waiting': False
        }
    ],
    'emergency_mode': False,
    'emergency_vehicle': None
}

# Normal traffic light cycle
def update_normal_traffic_lights(current_time):
    cycle = (current_time // 30) % 2
    if cycle == 0:
        traffic_data['traffic_lights'][0]['state'] = 'RED'    # North
        traffic_data['traffic_lights'][1]['state'] = 'GREEN'  # East
        traffic_data['traffic_lights'][2]['state'] = 'RED'    # South
        traffic_data['traffic_lights'][3]['state'] = 'GREEN'  # West
    else:
        traffic_data['traffic_lights'][0]['state'] = 'GREEN'  # North
        traffic_data['traffic_lights'][1]['state'] = 'RED'    # East
        traffic_data['traffic_lights'][2]['state'] = 'GREEN'  # South
        traffic_data['traffic_lights'][3]['state'] = 'RED'    # West
    
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
        
        # Here we'll just call our own endpoint (in a real system, this would go to vanetza)
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
    else:
        update_normal_traffic_lights(current_time)
    
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
        
        # If we reach here, it was not an emergency vehicle DENM
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
        speed_factor = 0.00006 * vehicle['speed'] / 30  # Scale factor for speed
        
        # Define lane offset (right side of road)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)