import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
    
    # EnOS 集成配置
    ENOS_API_BASE = os.getenv('ENOS_API_BASE', 'https://api.enos.com/edge')
    ENOS_API_KEY = os.getenv('ENOS_API_KEY')
    ENOS_ORG_ID = os.getenv('ENOS_ORG_ID')
    ENOS_ACCESS_KEY = os.getenv('ENOS_ACCESS_KEY')
    ENOS_SECRET_KEY = os.getenv('ENOS_SECRET_KEY')
    
    # 性能配置
    MAX_POINTS_PER_REQUEST = 1000
    BATCH_PROCESSING_TIMEOUT = 300  # seconds

class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False

class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True

class TestingConfig(Config):
    ENV = 'testing'
    DEBUG = True
    TESTING = True
    # Disable Celery for testing - run tasks synchronously to avoid needing broker
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'

# Configuration dictionary - maps environment names to Config classes
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 