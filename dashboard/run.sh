#!/bin/bash

# This script is used to run the dashboard application backend.
gnome-terminal -- bash -c "python3 server.py; exec bash"

# Wait 10 seconds.
sleep 5

# Open a new terminal for the npm front-end.
gnome-terminal -- bash -c "cd app; npm run start; exec bash"