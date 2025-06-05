# utils/middleware.py - Custom Middleware
from flask import request, g, jsonify, current_app
from functools import wraps
import time
import uuid
import json
from datetime import datetime

def request_middleware(app):
    """Setup request middleware"""
    
    @app.before_request
    def before_request_handler():
        """Handle before request operations"""
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())[:8]

        current_app.logger.info(
            f"[{g.request_id}] Incoming request: {request.method} {request.full_path}"
        )

        # Log request headers in debug mode
        if current_app.debug:
            headers = dict(request.headers)
            current_app.logger.debug(f"[{g.request_id}] Headers: {json.dumps(headers, indent=2)}")

        # # 🔒 Enforce API key in Authorization header
        # required_api_key = "Bearer 563@2323re2f2421fewkvn0913u4hfkenrwjlfmw"
        # auth_header = request.headers.get("Authorization")
        # if auth_header != required_api_key:
        #     current_app.logger.warning(
        #         f"[{g.request_id}] Unauthorized access attempt - Invalid or missing API key"
        #     )
        #     return jsonify({
        #         'error': 'Unauthorized. Invalid or missing API key.',
        #         'status_code': 401
        #     }), 401

        # Log request body for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            try:
                if current_app.debug:
                    current_app.logger.debug(f"[{g.request_id}] Request body: {request.get_json()}")
            except Exception as e:
                current_app.logger.warning(f"[{g.request_id}] Could not log request body: {str(e)}")

    @app.after_request
    def after_request_handler(response):
        """Handle after request operations"""
        # Calculate request duration
        duration = time.time() - g.get('start_time', time.time())
        
        # Add custom headers
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
        
        # Log response
        current_app.logger.info(
            f"[{g.get('request_id', 'unknown')}] Response: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        # Log slow requests
        if duration > 1.0:  # Log requests taking more than 1 second
            current_app.logger.warning(
                f"[{g.get('request_id', 'unknown')}] SLOW REQUEST: {request.method} {request.path} - "
                f"Duration: {duration:.3f}s"
            )
        
        return response

def require_json(f):
    """Decorator to require JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            current_app.logger.warning(f"Non-JSON request to {request.endpoint}")
            return jsonify({
                'error': 'Content-Type must be application/json',
                'status_code': 400
            }), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_json_fields(required_fields=None, optional_fields=None):
    """Decorator to validate JSON request fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type must be application/json',
                    'status_code': 400
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Invalid JSON data',
                    'status_code': 400
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    current_app.logger.warning(f"Missing required fields: {missing_fields}")
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields,
                        'status_code': 400
                    }), 400
            
            # Check for unexpected fields
            if optional_fields and required_fields:
                allowed_fields = set(required_fields + optional_fields)
                unexpected_fields = [field for field in data.keys() if field not in allowed_fields]
                if unexpected_fields:
                    current_app.logger.warning(f"Unexpected fields: {unexpected_fields}")
                    return jsonify({
                        'error': 'Unexpected fields in request',
                        'unexpected_fields': unexpected_fields,
                        'status_code': 400
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit_by_ip(max_requests=100, per_seconds=3600):
    """Simple in-memory rate limiting by IP (use Redis in production)"""
    request_counts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            cutoff_time = current_time - per_seconds
            request_counts[client_ip] = [
                timestamp for timestamp in request_counts.get(client_ip, [])
                if timestamp > cutoff_time
            ]
            
            # Check rate limit
            if len(request_counts.get(client_ip, [])) >= max_requests:
                current_app.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {per_seconds} seconds',
                    'status_code': 429
                }), 429
            
            # Add current request
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            request_counts[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_execution_time(f):
    """Decorator to log function execution time"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        execution_time = time.time() - start_time
        
        current_app.logger.info(
            f"Function {f.__name__} executed in {execution_time:.3f}s"
        )
        
        # Log to performance logger if available
        try:
            from .logger import log_performance
            log_performance(f.__name__, execution_time)
        except ImportError:
            pass
        
        return result
    return decorated_function