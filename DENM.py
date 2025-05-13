# Sample script to send DENM message from OBU to RSU
import requests
import json
import time

SERVER_URL = "http://localhost:3000/api/denm"

def send_emergency_denm(station_id, position, heading):
    """Send emergency DENM message to RSU server"""
    denm_message = {
        "header": {
            "protocolVersion": 1,
            "messageID": 1,  # DENM
            "stationID": station_id
        },
        "management": {
            "actionID": {
                "originatingStationID": station_id,
                "sequenceNumber": int(time.time()) % 65536
            },
            "detectionTime": int(time.time()),
            "referenceTime": int(time.time()),
            "eventPosition": {
                "latitude": position[0] * 10000000,  # Convert to decidegree
                "longitude": position[1] * 10000000
            },
            "validityDuration": 60,  # 60 seconds
            "stationType": 5  # Emergency vehicle
        },
        "situation": {
            "informationQuality": 7,  # High quality
            "eventType": {
                "causeCode": 6,  # Emergency vehicle approaching
                "subCauseCode": 1  # Emergency vehicle
            },
            "linkedCause": {
                "causeCode": 6,
                "subCauseCode": 0
            }
        },
        "location": {
            "eventPosition": {
                "latitude": position[0] * 10000000,
                "longitude": position[1] * 10000000
            },
            "eventPositionHeading": heading
        }
    }
    
    try:
        response = requests.post(SERVER_URL, json=denm_message)
        print(f"DENM sent. Response: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        print(f"Error sending DENM: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    # Ambulance station ID
    station_id = 12345
    
    # Position near the intersection (latitude, longitude)
    position = [40.6325, -8.6580]
    
    # Heading (in degrees, 0=North, 90=East, etc.)
    heading = 270  # West
    
    # Send DENM
    send_emergency_denm(station_id, position, heading)