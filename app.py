# app.py - Main Flask Application
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import time
import uuid

# Import blueprints for different services
from routes.health import health_bp
from routes.api_v1 import api_v1_bp
from routes.voice_assistant import voice_assistant_bp
from config import Config
from utils.logger import setup_logging
from utils.middleware import request_middleware

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Setup logging
    setup_logging(app)
    
    # Trust proxy headers (important for Render deployment)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Enable CORS - Accept requests from anywhere
    CORS(app, 
         origins=['*'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
         allow_headers=['*'],
         supports_credentials=True)
    
    # Register middleware
    request_middleware(app)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    app.register_blueprint(voice_assistant_bp, url_prefix='/api/v1/ai')
    
    # Error handlers
    register_error_handlers(app)
    
    # Request/Response logging
    register_request_logging(app)
    
    # Handle CORS preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({'status': 'ok'})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
            return response
    
    return app

def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f"404 Error: {request.url} - {request.remote_addr}")
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Error: {str(error)} - {request.url}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status_code': 500
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"400 Error: {str(error)} - {request.url}")
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid or malformed',
            'status_code': 400
        }), 400

def register_request_logging(app):
    """Register request/response logging"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())[:8]
        
        app.logger.info(
            f"[{g.request_id}] {request.method} {request.path} - "
            f"IP: {request.remote_addr} - "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
    
    @app.after_request
    def after_request(response):
        duration = time.time() - g.start_time
        app.logger.info(
            f"[{g.request_id}] Response: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        # Add custom headers
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # Ensure CORS headers for all responses
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = '*'
        
        return response

# Main entry point
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 6969))
    
    app.logger.info(f"Starting Flask server on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )