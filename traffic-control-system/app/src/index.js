from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic data
traffic_data = {
    'robots': [],
    'signals': []
}

@app.route('/update_traffic', methods=['POST'])
def update_traffic():
    data = request.get_json()
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

@app.route('/map', methods=['GET'])
def map_interface():
    # Serve a simple HTML page for the map interface
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Traffic Control System</title>
        <style>
            #map {
                height: 100vh;
                width: 100%;
            }
        </style>
        <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
        <script>
            function initMap() {
                var map = new google.maps.Map(document.getElementById('map'), {
                    zoom: 12,
                    center: {lat: -34.397, lng: 150.644} // Example coordinates
                });

                // Fetch traffic data and update the map
                fetch('/traffic_data')
                    .then(response => response.json())
                    .then(data => {
                        // Update map with robots and signals
                        data.robots.forEach(robot => {
                            new google.maps.Marker({
                                position: {lat: robot.lat, lng: robot.lng},
                                map: map,
                                title: 'Robot'
                            });
                        });

                        data.signals.forEach(signal => {
                            new google.maps.Marker({
                                position: {lat: signal.lat, lng: signal.lng},
                                map: map,
                                title: 'Signal'
                            });
                        });
                    });
            }
        </script>
    </head>
    <body onload="initMap()">
        <div id="map"></div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)