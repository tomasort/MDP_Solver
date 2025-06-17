#!/usr/bin/env python3
"""
MDP Solver Web Application Startup Script
"""

import os
import sys

def main():
    """Main entry point for the application"""
    # Set environment variables if not already set
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Import and run the app
    from app import app, config
    
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = config[config_name]
    
    print(f"Starting MDP Solver Web UI...")
    print(f"Environment: {config_name}")
    print(f"Debug mode: {config_obj.DEBUG}")
    print(f"Server running at: http://{config_obj.HOST}:{config_obj.PORT}")
    print(f"Press Ctrl+C to quit")
    
    app.run(
        debug=config_obj.DEBUG,
        host=config_obj.HOST,
        port=config_obj.PORT,
        use_reloader=config_obj.USE_RELOADER
    )

if __name__ == '__main__':
    main()
