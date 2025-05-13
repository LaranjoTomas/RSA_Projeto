# filepath: /home/laranjo/Desktop/RSA_Projeto/dashboard/server.py
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample data for traffic signals and robots
traffic_signals = {
    'signal_1': {'status': 'green', 'location': {'lat': 37.7749, 'lng': -122.4194}},
    'signal_2': {'status': 'red', 'location': {'lat': 37.7750, 'lng': -122.4184}},
}

robots = [
    {'id': 'robot_1', 'location': {'lat': 37.7751, 'lng': -122.4174}, 'status': 'active'},
    {'id': 'robot_2', 'location': {'lat': 37.7752, 'lng': -122.4164}, 'status': 'inactive'},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/traffic_signals', methods=['GET'])
def get_traffic_signals():
    return jsonify(traffic_signals)

@app.route('/robots', methods=['GET'])
def get_robots():
    return jsonify(robots)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)