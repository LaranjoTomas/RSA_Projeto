from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample data structure for traffic signals and robots
traffic_signals = {
    'signal_1': {'location': {'lat': 37.7749, 'lng': -122.4194}, 'status': 'green'},
    'signal_2': {'location': {'lat': 37.7849, 'lng': -122.4094}, 'status': 'red'},
}

robots = {
    'robot_1': {'location': {'lat': 37.7749, 'lng': -122.4294}, 'status': 'active'},
    'robot_2': {'location': {'lat': 37.7649, 'lng': -122.4194}, 'status': 'inactive'},
}

@app.route('/traffic_signals', methods=['GET'])
def get_traffic_signals():
    return jsonify(traffic_signals)

@app.route('/robots', methods=['GET'])
def get_robots():
    return jsonify(robots)

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    signal_id = data.get('signal_id')
    status = data.get('status')
    
    if signal_id in traffic_signals:
        traffic_signals[signal_id]['status'] = status
        return jsonify({'status': 'success', 'data': traffic_signals[signal_id]})
    else:
        return jsonify({'error': 'Signal not found'}), 404

@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    robot_id = data.get('robot_id')
    location = data.get('location')
    
    if robot_id in robots:
        robots[robot_id]['location'] = location
        return jsonify({'status': 'success', 'data': robots[robot_id]})
    else:
        return jsonify({'error': 'Robot not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)