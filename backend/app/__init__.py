"""
Personal AI Assistant Backend Application
Main Flask application factory and initialization.
"""

from flask import Flask
from flask_cors import CORS
import logging
from app.config import config

def create_app(config_name='default'):
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name (str): Configuration environment name
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Setup logging
    setup_logging(app)
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    app.logger.info('Personal AI Assistant backend started successfully')
    
    return app

def register_blueprints(app):
    """
    Register all application blueprints.
    
    Args:
        app (Flask): Flask application instance
    """
    from app.routes import chat_bp, voice_bp, health_bp
    
    app.register_blueprint(health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(chat_bp, url_prefix='/api/v1/chat')
    app.register_blueprint(voice_bp, url_prefix='/api/v1/voice')

def setup_logging(app):
    """
    Setup application logging configuration.
    
    Args:
        app (Flask): Flask application instance
    """
    if not app.debug:
        # Setup production logging
        logging.basicConfig(
            level=getattr(logging, app.config['LOG_LEVEL']),
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    else:
        # Development logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

def setup_error_handlers(app):
    """
    Setup global error handlers.
    
    Args:
        app (Flask): Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Endpoint not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400
