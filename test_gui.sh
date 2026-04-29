#!/bin/bash
# Test script to run GUI from correct directory
cd "/home/baxter/Desktop/workspace/Baxters HQ Sample Pack Generator"
source env/bin/activate
echo "=== Environment activated ==="
echo "Python: $(which python)"
echo "Working directory: $(pwd)"
echo "=== Launching GUI ===" 
python run_gui.py
