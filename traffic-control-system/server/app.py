# filepath: /home/laranjo/Desktop/RSA_Projeto/dashboard/server.py
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample data for robots and signals
robots = [
    {'id': 1, 'location': {'lat': 37.7749, 'lng': -122.4194}, 'status': 'active'},
    {'id': 2, 'location': {'lat': 37.7849, 'lng': -122.4094}, 'status': 'inactive'},
]

signals = [
    {'id': 1, 'location': {'lat': 37.7749, 'lng': -122.4294}, 'state': 'green'},
    {'id': 2, 'location': {'lat': 37.7849, 'lng': -122.4394}, 'state': 'red'},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/robots', methods=['GET'])
def get_robots():
    return jsonify(robots)

@app.route('/signals', methods=['GET'])
def get_signals():
    return jsonify(signals)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)