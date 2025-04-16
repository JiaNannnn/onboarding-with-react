import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    # Core settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = False
    TESTING = False
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # OpenAI configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4.1')
    
    # API configuration
    API_VERSION = '1.0.0'
    
    # EnOS integration configuration
    ENOS_API_BASE = os.environ.get('ENOS_API_BASE', 'https://api.enos.com/edge')
    ENOS_API_KEY = os.environ.get('ENOS_API_KEY')
    ENOS_ORG_ID = os.environ.get('ENOS_ORG_ID')
    ENOS_ACCESS_KEY = os.environ.get('ENOS_ACCESS_KEY')
    ENOS_SECRET_KEY = os.environ.get('ENOS_SECRET_KEY')
    
    # Performance configuration
    MAX_POINTS_PER_REQUEST = 1000
    BATCH_PROCESSING_TIMEOUT = 300  # seconds


class DevelopmentConfig(Config):
    """Development configuration."""
    ENV = 'development'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestingConfig(Config):
    """Testing configuration."""
    ENV = 'testing'
    TESTING = True
    DEBUG = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
    # Disable Celery for testing - run tasks synchronously
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    ENV = 'production'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Make sure to use a more secure broker in production
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')
    LOG_LEVEL = 'INFO'


# Map environment name to config class
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 