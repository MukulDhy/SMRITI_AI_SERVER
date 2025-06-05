# routes/health.py - Health Check Endpoints
from flask import Blueprint, jsonify, current_app
from datetime import datetime, timezone
import psutil
import os
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': current_app.config.get('API_VERSION', '1.0.0'),
        'environment': os.environ.get('FLASK_ENV', 'production')
    })

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application uptime (approximate)
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': current_app.config.get('API_VERSION', '1.0.0'),
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'system': {
                'cpu_usage_percent': cpu_percent,
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'usage_percent': memory.percent
                },
                'disk': {
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'usage_percent': round((disk.used / disk.total) * 100, 2)
                },
                'uptime_hours': round(uptime / 3600, 2)
            },
            'services': {
                'database': check_database_health(),
                'redis': check_redis_health(),
                'external_apis': check_external_apis_health()
            }
        }
        
        # Determine overall status
        services_status = [service['status'] for service in health_data['services'].values()]
        if all(status == 'healthy' for status in services_status):
            health_data['status'] = 'healthy'
        elif any(status == 'unhealthy' for status in services_status):
            health_data['status'] = 'degraded'
        else:
            health_data['status'] = 'unknown'
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        
        current_app.logger.info(f"Health check completed - Status: {health_data['status']}")
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/ready')
def readiness_check():
    """Kubernetes readiness probe endpoint"""
    try:
        # Check if application is ready to serve requests
        # Add your specific readiness checks here
        
        checks = {
            'database': check_database_health(),
            'configuration': check_configuration_health()
        }
        
        all_ready = all(check['status'] == 'healthy' for check in checks.values())
        
        if all_ready:
            return jsonify({
                'status': 'ready',
                'timestamp': datetime.utcnow().isoformat(),
                'checks': checks
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'timestamp': datetime.utcnow().isoformat(),
                'checks': checks
            }), 503
            
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@health_bp.route('/live')
def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

def check_database_health():
    """Check database connectivity"""
    try:
        # Add your database health check here
        # Example for SQLAlchemy:
        # from flask_sqlalchemy import SQLAlchemy
        # db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'message': 'Database connection successful',
            'response_time_ms': 0  # Add actual response time measurement
        }
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }

def check_redis_health():
    """Check Redis connectivity"""
    try:
        # Add your Redis health check here
        # Example:
        # import redis
        # r = redis.from_url(current_app.config['REDIS_URL'])
        # r.ping()
        
        return {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        current_app.logger.error(f"Redis health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }

def check_external_apis_health():
    """Check external API connectivity"""
    try:
        # Add checks for external APIs you depend on
        return {
            'status': 'healthy',
            'message': 'All external APIs accessible'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'External API check failed: {str(e)}'
        }

def check_configuration_health():
    """Check if all required configuration is present"""
    try:
        required_configs = ['SECRET_KEY']  # Add your required configs
        missing_configs = []
        
        for config in required_configs:
            if not current_app.config.get(config):
                missing_configs.append(config)
        
        if missing_configs:
            return {
                'status': 'unhealthy',
                'message': f'Missing required configuration: {missing_configs}'
            }
        
        return {
            'status': 'healthy',
            'message': 'All required configuration present'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Configuration check failed: {str(e)}'
        }