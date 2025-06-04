#!/bin/bash

# Start Dashboard Server
echo "Starting Dashboard Server..."
gnome-terminal -- bash -c "export TEST_NO_AMBULANCE=1; cd dashboard && python3 server.py; exec bash"
gnome-terminal -- bash -c "cd dashboard && cd app && npm run start; exec bash"

# sleep for 5 seconds

sleep 8

# Start RSU Publisher
echo "Starting RSU Publisher..."
gnome-terminal -- bash -c "cd rsu && python3 rsu_publisher.py; exec bash"

sleep 3

# Start Normal OBU
echo "Starting Normal OBU..."
gnome-terminal -- bash -c "cd normal_obu && python3 obu_normal.py; exec bash"

sleep 3

# Start Ambulance OBU
echo "Starting Ambulance OBU..."
gnome-terminal -- bash -c "cd ambulance_obu && python3 obu_ambulance.py; exec bash"