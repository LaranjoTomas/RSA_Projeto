from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Data structure to hold traffic signals and robot locations
traffic_signals = {
    'signal_1': {'status': 'red', 'location': {'lat': 37.7749, 'lng': -122.4194}},
    'signal_2': {'status': 'green', 'location': {'lat': 37.7750, 'lng': -122.4184}},
}

robots = {
    'robot_1': {'location': {'lat': 37.7749, 'lng': -122.4194}, 'status': 'active'},
    'robot_2': {'location': {'lat': 37.7751, 'lng': -122.4180}, 'status': 'inactive'},
}

@app.route('/traffic_signals', methods=['GET'])
def get_traffic_signals():
    return jsonify(traffic_signals)

@app.route('/robots', methods=['GET'])
def get_robots():
    return jsonify(robots)

@app.route('/update_signal/<signal_id>', methods=['POST'])
def update_signal(signal_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    if signal_id in traffic_signals:
        traffic_signals[signal_id]['status'] = data['status']
        return jsonify({'status': 'success', 'signal': traffic_signals[signal_id]})
    else:
        return jsonify({'error': 'Signal not found'}), 404

@app.route('/update_robot/<robot_id>', methods=['POST'])
def update_robot(robot_id):
    data = request.get_json()
    if not data or 'location' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    if robot_id in robots:
        robots[robot_id]['location'] = data['location']
        return jsonify({'status': 'success', 'robot': robots[robot_id]})
    else:
        return jsonify({'error': 'Robot not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)