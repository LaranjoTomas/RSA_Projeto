from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic control data
traffic_data = {
    'robots': [],
    'signals': []
}

@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update or add robot data
    robot_id = data.get('id')
    if robot_id is None:
        return jsonify({'error': 'Robot ID is required'}), 400

    # Check if robot already exists
    for robot in traffic_data['robots']:
        if robot['id'] == robot_id:
            robot.update(data)
            break
    else:
        traffic_data['robots'].append(data)

    return jsonify({'status': 'success', 'data': traffic_data['robots']})

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update or add signal data
    signal_id = data.get('id')
    if signal_id is None:
        return jsonify({'error': 'Signal ID is required'}), 400

    # Check if signal already exists
    for signal in traffic_data['signals']:
        if signal['id'] == signal_id:
            signal.update(data)
            break
    else:
        traffic_data['signals'].append(data)

    return jsonify({'status': 'success', 'data': traffic_data['signals']})

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(traffic_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)