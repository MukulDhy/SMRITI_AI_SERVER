# utils/logger.py - Logging Configuration
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import sys
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Add color to levelname
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        
        return super().format(record)

def setup_logging(app):
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    app.logger.setLevel(log_level)
    
    # Remove default handlers
    app.logger.handlers.clear()
    
    # Console handler with colors (for development)
    if app.config.get('DEBUG', False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        app.logger.addHandler(console_handler)
    
    # File handler (always active)
    file_handler = RotatingFileHandler(
        filename='logs/app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    file_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    app.logger.addHandler(file_handler)
    
    # Error file handler (for errors only)
    error_handler = RotatingFileHandler(
        filename='logs/error.log',
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    app.logger.addHandler(error_handler)
    
    # Performance log handler
    perf_handler = TimedRotatingFileHandler(
        filename='logs/performance.log',
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    perf_formatter = logging.Formatter(
        fmt='%(asctime)s - PERFORMANCE - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    perf_handler.setFormatter(perf_formatter)
    
    # Create performance logger
    perf_logger = logging.getLogger('performance')
    perf_logger.setLevel(logging.INFO)
    perf_logger.addHandler(perf_handler)
    
    # Log startup message
    app.logger.info(f"Logging initialized - Level: {app.config.get('LOG_LEVEL', 'INFO')}")
    app.logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    
    return app.logger

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)

def log_performance(func_name, duration, additional_info=None):
    """Log performance metrics"""
    perf_logger = logging.getLogger('performance')
    message = f"Function: {func_name} - Duration: {duration:.3f}s"
    if additional_info:
        message += f" - Info: {additional_info}"
    perf_logger.info(message)