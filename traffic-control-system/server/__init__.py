from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic signal and robot data
traffic_data = {
    'signals': [],
    'robots': []
}

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    if not data or 'id' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add traffic signal data
    signal = next((s for s in traffic_data['signals'] if s['id'] == data['id']), None)
    if signal:
        signal['status'] = data['status']
    else:
        traffic_data['signals'].append({
            'id': data['id'],
            'status': data['status']
        })

    return jsonify({'status': 'success', 'data': traffic_data['signals']})


@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    if not data or 'id' not in data or 'location' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add robot data
    robot = next((r for r in traffic_data['robots'] if r['id'] == data['id']), None)
    if robot:
        robot['location'] = data['location']
    else:
        traffic_data['robots'].append({
            'id': data['id'],
            'location': data['location']
        })

    return jsonify({'status': 'success', 'data': traffic_data['robots']})


@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(traffic_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)