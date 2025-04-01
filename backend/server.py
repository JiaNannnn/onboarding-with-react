#!/usr/bin/env python
"""
Simple server for BMS Points API

This is a minimal script to run the Flask app with debugging enabled.
"""
from app import create_app
from config import config_by_name

# Create the app with development config
app = create_app(config_by_name['development'])

if __name__ == "__main__":
    # Run the app with debug enabled
    print("Starting BMS Points API server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True) 