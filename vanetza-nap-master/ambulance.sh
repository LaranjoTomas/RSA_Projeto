#!/bin/bash
echo "[AMBULANCE] Starting socktap..."
socktap -c /config.ini > /var/log/socktap.log 2>&1 &

echo "[AMBULANCE] Installing dependencies..."
apt-get update && apt-get install -y python3 python3-pip
pip3 install paho-mqtt

echo "[AMBULANCE] Running cam_publisher.py..."
cd /ambulance_obu
python3 cam_publisher.py
