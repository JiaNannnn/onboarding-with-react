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
    
    # Create a file handler for detailed logs with UTF-8 encoding
    try:
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'api.log'), 
            maxBytes=10485760,  # 10MB
            backupCount=10,
            encoding='utf-8',  # Specify UTF-8 encoding
            delay=True  # Delay file creation until first log record is emitted
        )
    except Exception as e:
        print(f"Error creating log file handler: {str(e)}")
        # Fallback to a dummy handler if file access fails
        file_handler = logging.NullHandler()
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Create a console handler for immediate feedback with UTF-8 encoding
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.INFO)
    
    # Force UTF-8 encoding for console output
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
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
                                 "x-access-key", "x-secret-key", "AccessKey", "SecretKey", "Content-Length"],
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
    try:
        from .api import bp as api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
    except ImportError as e:
        app.logger.warning(f"API blueprint not found or failed to import, skipping API routes: {e}")
    except Exception as e:
        app.logger.error(f"Unexpected error registering API blueprint: {e}", exc_info=True)

    # Import and register BMS blueprint *after* app creation
    try:
        from .bms import bp as bms_bp # Use relative import here
        app.register_blueprint(bms_bp, url_prefix='/api/bms')
    except ImportError as e:
        app.logger.warning(f"BMS blueprint not found or failed to import, skipping BMS routes: {e}")
    except Exception as e:
        app.logger.error(f"Unexpected error registering BMS blueprint: {e}", exc_info=True)

    app.logger.info('API ready - blueprints registered')

    # Add a route to handle OPTIONS requests globally
    @app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def handle_options(path):
        response = app.make_default_options_response()
        return response

    return app 