import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polygon, Polyline, Marker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Vehicle marker component using proper Leaflet markers
const VehicleMarker = ({ position, vehicle }) => {
  const isEmergency = vehicle.type === 'ambulance';
  const isWaiting = vehicle.waiting;
  
  // Set vehicle color
  let fillColor = isEmergency ? '#ff0000' : '#0066ff';
  if (isWaiting) {
    fillColor = '#ff9900'; // Orange for waiting vehicles
  }
  
  // Create a custom icon for the vehicle
  const vehicleIcon = L.divIcon({
    className: 'vehicle-marker',
    html: `<div style="
      width: 20px;
      height: 12px;
      background-color: ${fillColor};
      border-radius: 4px;
      transform: rotate(${vehicle.heading}deg);
      transform-origin: center;
      border: 1px solid #000;
    "></div>`,
    iconSize: [20, 12],
    iconAnchor: [10, 6]
  });
  
  return (
    <Marker 
      position={position} 
      icon={vehicleIcon} 
    />
  );
};

const TrafficMap = () => {
  const [trafficData, setTrafficData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapCenter] = useState([40.6329, -8.6585]);
  const [zoom] = useState(17); // Reduced zoom level
  const serverUrl = 'http://localhost:3000';

  // Custom static map options
  const mapOptions = {
    attributionControl: false,
    zoomControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
  };

  // Fetch traffic data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${serverUrl}/api/traffic`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setTrafficData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
    const intervalId = setInterval(fetchData, 1000);
    
    return () => clearInterval(intervalId);
  }, [serverUrl]);

  const triggerEmergency = async (active = true) => {
    try {
      const response = await fetch(`${serverUrl}/api/emergency`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          vehicle_id: 'v_2',
          action: active ? 'activate' : 'deactivate'
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update emergency status');
      }
    } catch (err) {
      setError(err.message);
    }
  };
  
  const changeVehicleDirection = async (direction) => {
    try {
      const directionMap = {
        'North': 0,
        'East': 90,
        'South': 180,
        'West': 270
      };
      
      const response = await fetch(`${serverUrl}/api/vehicle/change-direction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vehicle_id: 'v_2',
          heading: directionMap[direction]
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to change direction');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div>Loading traffic data...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!trafficData) return <div>No traffic data available</div>;

  // Center of the intersection
  const center = mapCenter;
  
  // Calculate offset for road positions (longer roads)
  const offset = 0.008;  // Increased from 0.0008 to make roads longer
  
  // Define road polygons - wider and longer
  const roadWidth = 0.0004;
  
  // North road (vertical road, top part)
  const northRoad = [
    [center[0], center[1] - roadWidth/2], // Left edge
    [center[0], center[1] + roadWidth/2], // Right edge
    [center[0] + offset, center[1] + roadWidth/2], // Top right
    [center[0] + offset, center[1] - roadWidth/2], // Top left
  ];
  
  // South road (vertical road, bottom part)
  const southRoad = [
    [center[0], center[1] - roadWidth/2], // Left edge
    [center[0], center[1] + roadWidth/2], // Right edge
    [center[0] - offset, center[1] + roadWidth/2], // Bottom right
    [center[0] - offset, center[1] - roadWidth/2], // Bottom left
  ];
  
  // East road (horizontal road, right part)
  const eastRoad = [
    [center[0] - roadWidth/2, center[1]], // Top edge
    [center[0] + roadWidth/2, center[1]], // Bottom edge
    [center[0] + roadWidth/2, center[1] + offset], // Right bottom
    [center[0] - roadWidth/2, center[1] + offset], // Right top
  ];
  
  // West road (horizontal road, left part)
  const westRoad = [
    [center[0] - roadWidth/2, center[1]], // Top edge
    [center[0] + roadWidth/2, center[1]], // Bottom edge
    [center[0] + roadWidth/2, center[1] - offset], // Left bottom
    [center[0] - roadWidth/2, center[1] - offset], // Left top
  ];
  
  // Center divider lines - longer
  const northDivider = [
    [center[0], center[1]],
    [center[0] + offset * 0.95, center[1]]
  ];
  
  const southDivider = [
    [center[0], center[1]],
    [center[0] - offset * 0.95, center[1]]
  ];
  
  const eastDivider = [
    [center[0], center[1]],
    [center[0], center[1] + offset * 0.95]
  ];
  
  const westDivider = [
    [center[0], center[1]],
    [center[0], center[1] - offset * 0.95]
  ];

  // Get emergency state
  const isEmergencyMode = trafficData.emergency_mode;

  return (
    <div className="traffic-map-container">
      <div className="map-controls">
        <h2>Emergency Vehicle Controls</h2>
        <button 
          onClick={() => triggerEmergency(true)}
          className="emergency-button"
          disabled={isEmergencyMode}
        >
          Activate Emergency Mode
        </button>
        <button 
          onClick={() => triggerEmergency(false)}
          className="deactivate-button"
          disabled={!isEmergencyMode}
        >
          Deactivate Emergency Mode
        </button>
      </div>
      
      <div className="direction-controls">
        <h3>Change Direction:</h3>
        <div className="direction-buttons">
          <button 
            onClick={() => changeVehicleDirection('North')}
            className="direction-button"
          >
            North
          </button>
          <button 
            onClick={() => changeVehicleDirection('East')}
            className="direction-button"
          >
            East
          </button>
          <button 
            onClick={() => changeVehicleDirection('South')}
            className="direction-button"
          >
            South
          </button>
          <button 
            onClick={() => changeVehicleDirection('West')}
            className="direction-button"
          >
            West
          </button>
        </div>
      </div>
      
      <div className="map-container" style={{ height: '600px', borderRadius: '8px' }}>
        <MapContainer 
          center={mapCenter} 
          zoom={zoom} 
          style={{ height: '100%', width: '100%', backgroundColor: '#8cbe8c' }}
          {...mapOptions}
        >
          {/* Draw roads */}
          <Polygon positions={northRoad} pathOptions={{ fillColor: '#555', fillOpacity: 1, weight: 1, color: '#333' }} />
          <Polygon positions={southRoad} pathOptions={{ fillColor: '#555', fillOpacity: 1, weight: 1, color: '#333' }} />
          <Polygon positions={eastRoad} pathOptions={{ fillColor: '#555', fillOpacity: 1, weight: 1, color: '#333' }} />
          <Polygon positions={westRoad} pathOptions={{ fillColor: '#555', fillOpacity: 1, weight: 1, color: '#333' }} />
          
          {/* Draw road dividers */}
          <Polyline positions={northDivider} pathOptions={{ color: 'white', weight: 2, dashArray: '5, 10' }} />
          <Polyline positions={southDivider} pathOptions={{ color: 'white', weight: 2, dashArray: '5, 10' }} />
          <Polyline positions={eastDivider} pathOptions={{ color: 'white', weight: 2, dashArray: '5, 10' }} />
          <Polyline positions={westDivider} pathOptions={{ color: 'white', weight: 2, dashArray: '5, 10' }} />
          
          {/* Draw intersection center */}
          <CircleMarker 
            center={center} 
            radius={15}
            pathOptions={{ fillColor: '#555', fillOpacity: 1, color: '#333', weight: 1 }}
          />
          
          {/* Draw traffic lights */}
          {trafficData.traffic_lights.map(light => (
            <CircleMarker
              key={light.id}
              center={[light.position.lat, light.position.lng]}
              radius={8}
              pathOptions={{
                fillColor: light.state === 'RED' ? 'red' : 'green',
                fillOpacity: 1,
                color: 'white',
                weight: 2
              }}
            />
          ))}
          
          {/* Draw vehicles */}
          {trafficData.vehicles.map(vehicle => (
            <VehicleMarker
              key={vehicle.id}
              position={[vehicle.position.lat, vehicle.position.lng]}
              vehicle={vehicle}
            />
          ))}
        </MapContainer>
      </div>
      
      <div className="intersection-status">
        <h3>Intersection Status</h3>
        <div className="status-indicator">
          Emergency Mode: <span className={isEmergencyMode ? "active" : "inactive"}>
            {isEmergencyMode ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>
      
      <div className="map-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: 'red' }}></div>
          <div>Red Light</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: 'green' }}></div>
          <div>Green Light</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#0066ff' }}></div>
          <div>Regular Vehicle</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ff0000' }}></div>
          <div>Emergency Vehicle</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#ff9900' }}></div>
          <div>Vehicle Waiting at Red Light</div>
        </div>
      </div>
    </div>
  );
};

export default TrafficMap;