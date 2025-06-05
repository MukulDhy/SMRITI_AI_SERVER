# routes/api_v1.py - Main API Routes
from flask import Blueprint, jsonify, request, current_app
from utils.middleware import require_json, validate_json_fields, rate_limit_by_ip, log_execution_time
from datetime import datetime
import time

api_v1_bp = Blueprint('api_v1', __name__)

@api_v1_bp.route('/')
def api_info():
    """API information endpoint"""
    return jsonify({
        'api': current_app.config.get('API_TITLE', 'Flask API'),
        'version': current_app.config.get('API_VERSION', '1.0.0'),
        'description': current_app.config.get('API_DESCRIPTION', 'Professional Flask API'),
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'health': '/health',
            'api_info': '/api/v1/',
            'echo': '/api/v1/echo',
            'users': '/api/v1/users',
            'data_processing': '/api/v1/process'
        }
    })

@api_v1_bp.route('/echo', methods=['POST'])
@require_json
@validate_json_fields(required_fields=['message'])
@rate_limit_by_ip(max_requests=50, per_seconds=3600)
@log_execution_time
def echo():
    """Echo service - returns the input message with metadata"""
    try:
        data = request.get_json()
        message = data.get('message')
        
        current_app.logger.info(f"Echo request received: {message[:100]}...")
        
        response = {
            'status': 'success',
            'original_message': message,
            'echo': message,
            'timestamp': datetime.utcnow().isoformat(),
            'character_count': len(message),
            'word_count': len(message.split()),
            'request_id': request.headers.get('X-Request-ID', 'unknown')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Echo service error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_v1_bp.route('/users', methods=['GET'])
@rate_limit_by_ip(max_requests=100, per_seconds=3600)
@log_execution_time
def get_users():
    """Get users - Example endpoint for user management"""
    try:
        # Example user data - replace with actual database query
        users = [
            {
                'id': 1,
                'name': 'John Doe',
                'email': 'john@example.com',
                'created_at': '2024-01-01T00:00:00Z',
                'active': True
            },
            {
                'id': 2,
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'created_at': '2024-01-02T00:00:00Z',
                'active': True
            }
        ]
        
        current_app.logger.info(f"Retrieved {len(users)} users")
        
        return jsonify({
            'status': 'success',
            'data': users,
            'count': len(users),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get users error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve users',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_v1_bp.route('/users', methods=['POST'])
@require_json
@validate_json_fields(required_fields=['name', 'email'], optional_fields=['phone', 'address'])
@rate_limit_by_ip(max_requests=20, per_seconds=3600)
@log_execution_time
def create_user():
    """Create new user - Example endpoint"""
    try:
        data = request.get_json()
        
        # Validate email format (basic validation)
        email = data.get('email')
        if '@' not in email:
            return jsonify({
                'status': 'error',
                'message': 'Invalid email format',
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        # Example user creation - replace with actual database logic
        new_user = {
            'id': int(time.time()),  # Simple ID generation
            'name': data.get('name'),
            'email': email,
            'phone': data.get('phone'),
            'address': data.get('address'),
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
        
        current_app.logger.info(f"Created new user: {new_user['email']}")
        
        return jsonify({
            'status': 'success',
            'message': 'User created successfully',
            'data': new_user,
            'timestamp': datetime.utcnow().isoformat()
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Create user error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to create user',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_v1_bp.route('/process', methods=['POST'])
@require_json
@validate_json_fields(required_fields=['data', 'operation'], optional_fields=['options'])
@rate_limit_by_ip(max_requests=30, per_seconds=3600)
@log_execution_time
def process_data():
    """Data processing service - Example for adding custom processing logic"""
    try:
        request_data = request.get_json()
        data = request_data.get('data')
        operation = request_data.get('operation')
        options = request_data.get('options', {})
        
        current_app.logger.info(f"Processing data with operation: {operation}")
        
        # Example processing operations
        result = None
        if operation == 'count':
            if isinstance(data, list):
                result = len(data)
            elif isinstance(data, str):
                result = len(data)
            else:
                result = 1
                
        elif operation == 'reverse':
            if isinstance(data, list):
                result = list(reversed(data))
            elif isinstance(data, str):
                result = data[::-1]
            else:
                result = data
                
        elif operation == 'uppercase':
            if isinstance(data, str):
                result = data.upper()
            elif isinstance(data, list):
                result = [str(item).upper() if isinstance(item, str) else item for item in data]
            else:
                result = str(data).upper()
                
        elif operation == 'sum':
            if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
                result = sum(data)
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Sum operation requires a list of numbers',
                    'timestamp': datetime.utcnow().isoformat()
                }), 400
                
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unknown operation: {operation}',
                'supported_operations': ['count', 'reverse', 'uppercase', 'sum'],
                'timestamp': datetime.utcnow().isoformat()
            }), 400
        
        response = {
            'status': 'success',
            'operation': operation,
            'original_data': data,
            'result': result,
            'options_used': options,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        current_app.logger.info(f"Data processing completed: {operation}")
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Data processing error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Data processing failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@api_v1_bp.route('/status', methods=['GET'])
def api_status():
    """API status endpoint with detailed metrics"""
    try:
        return jsonify({
            'status': 'operational',
            'version': current_app.config.get('API_VERSION', '1.0.0'),
            'environment': current_app.config.get('FLASK_ENV', 'production'),
            'debug_mode': current_app.debug,
            'timestamp': datetime.utcnow().isoformat(),
            'server_time': datetime.now().isoformat(),
            'uptime': 'Available in /health/detailed endpoint',
            'features': {
                'rate_limiting': True,
                'request_logging': True,
                'error_handling': True,
                'cors_enabled': True,
                'json_validation': True
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Status endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get status',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Error handlers specific to API v1
@api_v1_bp.errorhandler(404)
def api_not_found(error):
    """Handle 404 errors in API v1"""
    return jsonify({
        'status': 'error',
        'message': 'API endpoint not found',
        'available_endpoints': [
            '/api/v1/',
            '/api/v1/echo',
            '/api/v1/users',
            '/api/v1/process',
            '/api/v1/status'
        ],
        'timestamp': datetime.utcnow().isoformat()
    }), 404

@api_v1_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed for this endpoint',
        'timestamp': datetime.utcnow().isoformat()
    }), 405