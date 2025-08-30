"""
Main entry point for the Personal AI Assistant Flask application.
"""

import os
from app import create_app
from app.config import config

def main():
    """Main function to run the Flask application."""
    
    # Get environment from environment variable or default to development
    env = os.environ.get('FLASK_ENV', 'development')
    
    # Validate environment
    if env not in config:
        print(f"Unknown environment: {env}. Using development.")
        env = 'development'
    
    # Create Flask app
    app = create_app(env)
    
    # Validate configuration
    try:
        config[env].validate_config()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"⚠️  Configuration warning: {e}")
        print("Some features may not work properly without proper API keys.")
    
    # Get host and port from config
    host = app.config.get('HOST', 'localhost')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', False)
    
    print(f"🚀 Starting Personal AI Assistant API")
    print(f"📍 Environment: {env}")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
    print(f"📋 Available endpoints:")
    print(f"   • Health: http://{host}:{port}/api/v1/health/")
    print(f"   • Chat: http://{host}:{port}/api/v1/chat/message")
    print(f"   • Voice: http://{host}:{port}/api/v1/voice/speech-to-text")
    print(f"   • Detailed health: http://{host}:{port}/api/v1/health/detailed")
    
    # Run the application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True  # Enable threading for better performance
    )

if __name__ == '__main__':
    main()
