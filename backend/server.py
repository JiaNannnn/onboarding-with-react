#!/usr/bin/env python
"""
Simple server for BMS Points API

This is a minimal script to run the Flask app with debugging enabled.
"""
import sys
import traceback
from flask import Flask
from app.config import config_by_name
from app import create_app

# Enhanced error handling
def main():
    try:
        print("Starting Flask server...")
        app = create_app(config_by_name['development'])
        print("Flask app created successfully!")
        app.run(host='0.0.0.0', debug=True)
    except Exception as e:
        print(f"ERROR: Failed to start server: {str(e)}")
        print("Traceback:")
        traceback.print_exc()
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main()) 