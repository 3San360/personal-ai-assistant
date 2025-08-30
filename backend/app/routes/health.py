"""
Health check routes for the Personal AI Assistant API.
"""

from flask import Blueprint, jsonify
from datetime import datetime
import sys
import os

from app.config import Config

health_bp = Blueprint('health', __name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Personal AI Assistant API',
        'version': '1.0.0'
    })

@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with service status.
    
    Returns:
        JSON response with detailed health information
    """
    health_info = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'Personal AI Assistant API',
        'version': '1.0.0',
        'python_version': sys.version,
        'environment': Config.ENV if hasattr(Config, 'ENV') else 'unknown',
        'services': {}
    }
    
    # Check external services
    services_status = {}
    
    # Weather service check
    if Config.OPENWEATHER_API_KEY:
        services_status['weather'] = 'configured'
    else:
        services_status['weather'] = 'not_configured'
    
    # News service check
    if Config.NEWS_API_KEY:
        services_status['news'] = 'configured'
    else:
        services_status['news'] = 'not_configured'
    
    # Calendar service check
    if Config.GOOGLE_CALENDAR_CREDENTIALS_FILE and os.path.exists(Config.GOOGLE_CALENDAR_CREDENTIALS_FILE):
        services_status['calendar'] = 'configured'
    elif Config.GOOGLE_CALENDAR_CREDENTIALS_FILE:
        services_status['calendar'] = 'credentials_file_missing'
    else:
        services_status['calendar'] = 'not_configured'
    
    health_info['services'] = services_status
    
    # Determine overall status
    if any(status == 'not_configured' for status in services_status.values()):
        health_info['status'] = 'degraded'
    
    return jsonify(health_info)

@health_bp.route('/ping', methods=['GET'])
def ping():
    """
    Simple ping endpoint for load balancers.
    
    Returns:
        Plain text "pong" response
    """
    return "pong", 200
