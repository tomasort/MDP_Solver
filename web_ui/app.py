import os
import sys
from flask import Flask

# Import blueprints
from blueprints.main import main_bp
from blueprints.api import api_bp
from blueprints.errors import errors_bp
from config import config

def create_app(config_name=None):
    """Application factory pattern for creating Flask app"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(errors_bp)
    
    return app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    config_name = os.environ.get('FLASK_ENV', 'development')
    config_obj = config[config_name]
    
    app.run(
        debug=config_obj.DEBUG,
        host=config_obj.HOST,
        port=config_obj.PORT,
        use_reloader=config_obj.USE_RELOADER
    )
