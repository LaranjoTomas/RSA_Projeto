# filepath: /home/laranjo/Desktop/RSA_Projeto/dashboard/server.py
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import random
import time

app = Flask(__name__)
CORS(app)

# Sample data for traffic control system
traffic_data = {
    'robots': [],
    'signals': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_traffic', methods=['POST'])
def update_traffic():
    data = request.get_json()
    print("Received traffic data:", data)
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Update the traffic data store
    traffic_data['robots'] = data.get('robots', [])
    traffic_data['signals'] = data.get('signals', [])
    
    print("Updated traffic data:", traffic_data)
    return jsonify({'status': 'success', 'data': traffic_data})

@app.route('/traffic_data', methods=['GET'])
def get_traffic_data():
    return jsonify(traffic_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)