from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time

app = Flask(__name__)
CORS(app)

# Global variable to store sensor data received from the ESP device.

# current_sensor_data = {}

current_sensor_data = {
    'bme_temperature': 10.0,
    'bme_pressure': 0.0,
    'bme_humidity': 0.0,
    'tc74_temperature': 0,
    'timestamp': 0
}
# @app.route('/update', methods=['POST'])
# def update():
#     global current_sensor_data
#     data = request.get_json()
#     if not data:
#         return jsonify({"error": "No data provided"}), 400
#     current_sensor_data = data
#     print("Updated sensor data:", current_sensor_data)
#     return jsonify({"status": "success"})

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    print("Received data:", data)
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update the global sensor data store.
    current_sensor_data.update({
        'bme_temperature': data.get('bme_temperature', 10.0),
        'bme_pressure': data.get('bme_pressure', 0.0),
        'bme_humidity': data.get('bme_humidity', 0.0),
        'tc74_temperature': data.get('tc74_temperature', 0),
        'timestamp': data.get('timestamp', 0)
    })
    print("Updated sensor data:", current_sensor_data)
    return jsonify({'status': 'success', 'data': current_sensor_data})

@app.route('/data', methods=['GET'])
def data():
    return jsonify(current_sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
