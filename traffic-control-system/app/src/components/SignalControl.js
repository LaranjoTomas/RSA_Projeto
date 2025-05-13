from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic control data
traffic_control_data = {
    'signals': [],
    'robots': []
}

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    if not data or 'id' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add traffic signal data
    signal = next((s for s in traffic_control_data['signals'] if s['id'] == data['id']), None)
    if signal:
        signal['status'] = data['status']
    else:
        traffic_control_data['signals'].append({
            'id': data['id'],
            'status': data['status'],
            'location': data.get('location', {})
        })

    return jsonify({'status': 'success', 'data': traffic_control_data})

@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    if not data or 'id' not in data or 'location' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add robot data
    robot = next((r for r in traffic_control_data['robots'] if r['id'] == data['id']), None)
    if robot:
        robot['location'] = data['location']
    else:
        traffic_control_data['robots'].append({
            'id': data['id'],
            'location': data['location']
        })

    return jsonify({'status': 'success', 'data': traffic_control_data})

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(traffic_control_data)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Traffic Control System</title>
        <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
        <script>
            function initMap() {
                const map = new google.maps.Map(document.getElementById("map"), {
                    zoom: 12,
                    center: { lat: -34.397, lng: 150.644 },
                });

                // Fetch traffic control data and update the map
                fetch('/data')
                    .then(response => response.json())
                    .then(data => {
                        data.signals.forEach(signal => {
                            new google.maps.Marker({
                                position: signal.location,
                                map: map,
                                title: `Signal ${signal.id}: ${signal.status}`
                            });
                        });

                        data.robots.forEach(robot => {
                            new google.maps.Marker({
                                position: robot.location,
                                map: map,
                                title: `Robot ${robot.id}`
                            });
                        });
                    });
            }
        </script>
    </head>
    <body onload="initMap()">
        <h1>Traffic Control System</h1>
        <div id="map" style="height: 500px; width: 100%;"></div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)