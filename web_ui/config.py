"""Configuration settings for the MDP Solver Web Application"""

import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mdp-solver-dev-key-2025'
    DEBUG = True
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5003
    USE_RELOADER = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    USE_RELOADER = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
