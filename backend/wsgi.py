#!/usr/bin/env python
from app import create_app
from config import ProductionConfig

# Create the application instance
app = create_app(ProductionConfig)

# For running directly
if __name__ == '__main__':
    app.run() 