"""Error handling blueprint"""

from flask import Blueprint, jsonify, render_template, request

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@errors_bp.app_errorhandler(400)
def bad_request_error(error):
    """Handle 400 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Bad request'}), 400
    return render_template('errors/400.html'), 400
