from flask import Flask
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_swagger_ui import get_swaggerui_blueprint

try:
    from flask_celery_helper import make_celery
    celery = make_celery()
except ImportError:
    from celery import Celery
    celery = Celery()
    print("WARNING: flask_celery_helper not found, using regular Celery for testing")

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        # Default to development config if none specified
        from config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    elif isinstance(config_class, str):
        # Load by string reference (e.g. "config.DevelopmentConfig")
        app.config.from_object(config_class)
    else:
        # Load directly from class
        app.config.from_object(config_class)
    
    # Configure logging
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create a file handler for detailed logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'api.log'), 
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Create a console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.INFO)
    
    # Add the handlers to the app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('API startup - logging configured')
    
    # Enable CORS for all routes with proper preflight support
    CORS(app, 
         resources={
             r"/*": {
                 "origins": ["http://localhost:3000", "http://10.230.80.86:3000"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Access-Control-Allow-Origin", 
                                 "x-access-key", "x-secret-key", "AccessKey", "SecretKey"],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True,
                 "send_wildcard": False,
                 "max_age": 3600
             }
         })

    # Register the request logging middleware
    try:
        from app.middleware import RequestLogger
        app.before_request(RequestLogger.before_request)
        app.after_request(RequestLogger.after_request)
    except ImportError:
        app.logger.warning("RequestLogger middleware not found, skipping request logging setup")

    celery.conf.update(app.config)

    # Configure Swagger UI
    SWAGGER_URL = '/docs'  # URL for exposing Swagger UI
    API_URL = '/static/swagger.yaml'  # Our API url
    
    # Create Swagger UI blueprint
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "BMS Points API",
            'layout': 'BaseLayout',
            'deepLinking': True,
            'displayRequestDuration': True,
            'defaultModelsExpandDepth': 3,
            'defaultModelExpandDepth': 3,
            'defaultModelRendering': 'model',
            'displayOperationId': False,
            'docExpansion': 'list',
            'showExtensions': True,
            'showCommonExtensions': True
        }
    )
    
    # Register blueprints
    app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)
    
    # Ensure the static directory exists
    static_dir = os.path.join(app.root_path, 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Copy swagger.yaml to static directory
    swagger_source = os.path.join(app.root_path, 'api', 'swagger.yaml')
    swagger_dest = os.path.join(static_dir, 'swagger.yaml')
    if os.path.exists(swagger_source):
        try:
            import shutil
            shutil.copy2(swagger_source, swagger_dest)
        except PermissionError:
            app.logger.warning("Permission error when copying swagger.yaml - skipping this step")
            # Try a different approach
            try:
                with open(swagger_source, 'r') as src:
                    content = src.read()
                    with open(swagger_dest, 'w') as dst:
                        dst.write(content)
                app.logger.info("Copied swagger.yaml content using file read/write")
            except Exception as e:
                app.logger.warning(f"Could not copy swagger.yaml: {str(e)}")
        except Exception as e:
            app.logger.warning(f"Error copying swagger.yaml: {str(e)}")

    # Register blueprints
    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    try:
        from app.bms import bp as bms_bp
        # Register BMS blueprint at both '/api/bms' and '/bms' prefixes
        app.register_blueprint(bms_bp, url_prefix='/api/bms')
        app.register_blueprint(bms_bp, url_prefix='/bms', name='bms_root')
    except ImportError:
        app.logger.warning("BMS blueprint not found, skipping BMS routes")

    app.logger.info('API ready - blueprints registered')
    return app 