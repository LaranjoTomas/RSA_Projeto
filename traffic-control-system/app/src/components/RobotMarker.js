from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic data
traffic_data = {
    'robots': [],
    'signals': []
}

@app.route('/')
def index():
    return render_template('index.html')  # Serve the main HTML page

@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    if not data or 'id' not in data or 'location' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add robot data
    robot_id = data['id']
    location = data['location']

    # Check if robot already exists
    for robot in traffic_data['robots']:
        if robot['id'] == robot_id:
            robot['location'] = location
            break
    else:
        # Add new robot if it doesn't exist
        traffic_data['robots'].append({'id': robot_id, 'location': location})

    return jsonify({'status': 'success', 'data': traffic_data['robots']})

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    if not data or 'id' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    signal_id = data['id']
    status = data['status']

    # Update or add signal data
    for signal in traffic_data['signals']:
        if signal['id'] == signal_id:
            signal['status'] = status
            break
    else:
        # Add new signal if it doesn't exist
        traffic_data['signals'].append({'id': signal_id, 'status': status})

    return jsonify({'status': 'success', 'data': traffic_data['signals']})

@app.route('/traffic_data', methods=['GET'])
def get_traffic_data():
    return jsonify(traffic_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)