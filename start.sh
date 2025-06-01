#!/bin/bash

# Start Dashboard Server
echo "Starting Dashboard Server..."
gnome-terminal -- bash -c "export TEST_NO_AMBULANCE=1; cd dashboard && python3 server.py; exec bash"
gnome-terminal -- bash -c "cd dashboard && cd app && npm run start; exec bash"

# Start RSU Publisher
echo "Starting RSU Publisher..."
gnome-terminal -- bash -c "cd rsu && python3 rsu_publisher.py; exec bash"

# Start Ambulance OBU
echo "Starting Ambulance OBU..."
gnome-terminal -- bash -c "cd ambulance_obu && python3 obu_ambulance.py; exec bash"