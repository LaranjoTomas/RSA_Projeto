### New Flask Server Implementation

```python
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global variable to store traffic data
traffic_data = {
    'robots': [],
    'signals': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_robot', methods=['POST'])
def update_robot():
    data = request.get_json()
    if not data or 'id' not in data or 'location' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Update or add robot data
    robot_id = data['id']
    location = data['location']
    
    # Check if robot already exists
    for robot in traffic_data['robots']:
        if robot['id'] == robot_id:
            robot['location'] = location
            break
    else:
        # Add new robot
        traffic_data['robots'].append({'id': robot_id, 'location': location})

    return jsonify({'status': 'success', 'data': traffic_data})

@app.route('/update_signal', methods=['POST'])
def update_signal():
    data = request.get_json()
    if not data or 'id' not in data or 'status' not in data:
        return jsonify({'error': 'Invalid data provided'}), 400

    signal_id = data['id']
    status = data['status']

    # Update or add signal data
    for signal in traffic_data['signals']:
        if signal['id'] == signal_id:
            signal['status'] = status
            break
    else:
        # Add new signal
        traffic_data['signals'].append({'id': signal_id, 'status': status})

    return jsonify({'status': 'success', 'data': traffic_data})

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(traffic_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
```

### HTML Template (index.html)

You will also need an HTML file to serve as the frontend. Create a folder named `templates` in the same directory as your `server.py` file and add the following `index.html` file:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Control System</title>
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY"></script>
    <style>
        #map {
            height: 500px;
            width: 100%;
        }
    </style>
</head>
<body>
    <h1>Traffic Control System</h1>
    <div id="map"></div>
    <script>
        let map;
        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: {lat: -34.397, lng: 150.644},
                zoom: 8
            });
        }

        // Fetch traffic data and update map
        async function fetchTrafficData() {
            const response = await fetch('/data');
            const data = await response.json();
            updateMap(data);
        }

        function updateMap(data) {
            // Clear existing markers
            // Add robots and signals to the map
            data.robots.forEach(robot => {
                new google.maps.Marker({
                    position: robot.location,
                    map: map,
                    title: `Robot ${robot.id}`
                });
            });

            data.signals.forEach(signal => {
                // Add signal markers or icons based on status
                new google.maps.Marker({
                    position: signal.location, // Assuming signal has a location
                    map: map,
                    title: `Signal ${signal.id} - ${signal.status}`
                });
            });
        }

        window.onload = () => {
            initMap();
            fetchTrafficData();
        };
    </script>
</body>
</html>
```

### Notes:
1. **Google Maps API Key**: Replace `YOUR_API_KEY` in the HTML template with your actual Google Maps API key.
2. **Data Structure**: The `traffic_data` structure is designed to hold robot and signal information. You can expand it as needed.
3. **Frontend Functionality**: The frontend fetches traffic data and updates the map with robot and signal locations. You may need to implement additional logic to handle signal locations and statuses.
4. **Testing**: Make sure to test the server and the frontend to ensure they work together as expected.

This implementation provides a basic framework for a traffic control system with a Google Maps-like interface. You can further enhance it by adding more features, such as real-time updates, user interactions, and more sophisticated data handling.