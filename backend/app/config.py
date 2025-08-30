"""
Configuration module for the Personal AI Assistant backend.
Handles environment variables and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('HOST', 'localhost')
    PORT = int(os.environ.get('PORT', 5000))
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:4200').split(',')
    
    # API Keys
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    
    # Google Calendar settings
    GOOGLE_CALENDAR_CREDENTIALS_FILE = os.environ.get('GOOGLE_CALENDAR_CREDENTIALS_FILE')
    GOOGLE_CALENDAR_TOKEN_FILE = os.environ.get('GOOGLE_CALENDAR_TOKEN_FILE', 'token.json')
    
    # Voice settings
    VOICE_RATE = int(os.environ.get('VOICE_RATE', 200))
    VOICE_VOLUME = float(os.environ.get('VOICE_VOLUME', 0.9))
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 60))
    
    # Cache settings
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration values are present."""
        required_keys = ['OPENWEATHER_API_KEY', 'NEWS_API_KEY']
        missing_keys = []
        
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")
        
        return True

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    ENV = 'testing'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
