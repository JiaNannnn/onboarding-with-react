#!/usr/bin/env python
from app import create_app
from app.config import ProductionConfig

# Create the application instance
application = create_app(ProductionConfig)

# For running directly
if __name__ == '__main__':
    application.run() 