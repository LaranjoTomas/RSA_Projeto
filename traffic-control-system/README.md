# Global variable to store traffic data
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
```

### Explanation of the Code:

1. **Flask Setup**: The Flask app is initialized, and CORS is enabled to allow cross-origin requests.

2. **Traffic Data Structure**: A global variable `traffic_data` is defined to store information about robots and signals.

3. **Index Route**: The root route (`/`) serves an HTML page (which we will create next) that will contain the Google Maps interface.

4. **Update Traffic Route**: The `/update_traffic` route accepts POST requests with JSON data to update the traffic data. It expects a structure that includes lists of robots and signals.

5. **Get Traffic Data Route**: The `/traffic_data` route returns the current traffic data in JSON format.

### Frontend Integration (HTML Template)

Next, create a simple HTML file named `index.html` in a `templates` folder:

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
            height: 100vh;
            width: 100%;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        let map;
        function initMap() {
            map = new google.maps.Map(document.getElementById('map'), {
                center: { lat: -34.397, lng: 150.644 },
                zoom: 8
            });
            fetchTrafficData();
        }

        function fetchTrafficData() {
            fetch('/traffic_data')
                .then(response => response.json())
                .then(data => {
                    console.log(data);
                    // Here you can add logic to place markers for robots and signals on the map
                });
        }

        window.onload = initMap;
    </script>
</body>
</html>
```

### Explanation of the HTML:

1. **Google Maps API**: The script tag includes the Google Maps JavaScript API. Replace `YOUR_API_KEY` with your actual Google Maps API key.

2. **Map Initialization**: The `initMap` function initializes the map and sets its center and zoom level.

3. **Fetching Traffic Data**: The `fetchTrafficData` function retrieves the traffic data from the Flask server and logs it to the console. You can extend this function to place markers on the map based on the robot and signal data.

### Final Steps:

1. **Run the Flask Server**: Start the Flask server by running the Python script.
2. **Access the Interface**: Open a web browser and navigate to `http://localhost:3000` to see the Google Maps interface.

This implementation provides a foundation for a traffic control system with robots and intelligent signaling, which can be further developed with additional features and functionalities.