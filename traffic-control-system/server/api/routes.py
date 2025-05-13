from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic control data
traffic_control_data = {
    'robots': [],
    'signals': []
}

@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    if not data or 'id' not in data or 'location' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add robot data
    robot_id = data['id']
    location = data['location']

    # Check if robot already exists
    for robot in traffic_control_data['robots']:
        if robot['id'] == robot_id:
            robot['location'] = location
            break
    else:
        # Add new robot
        traffic_control_data['robots'].append({'id': robot_id, 'location': location})

    return jsonify({'status': 'success', 'data': traffic_control_data})

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    if not data or 'id' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    signal_id = data['id']
    status = data['status']

    # Update or add signal data
    for signal in traffic_control_data['signals']:
        if signal['id'] == signal_id:
            signal['status'] = status
            break
    else:
        # Add new signal
        traffic_control_data['signals'].append({'id': signal_id, 'status': status})

    return jsonify({'status': 'success', 'data': traffic_control_data})

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(traffic_control_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)