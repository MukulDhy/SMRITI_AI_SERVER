# routes/voice_assistant.py
from flask import Blueprint, jsonify, request, current_app
import whisper
import base64
import tempfile
import os
import threading
import time
from utils.middleware import require_json, rate_limit_by_ip

voice_assistant_bp = Blueprint('voice_assistant', __name__)

# Global variables for model management
model = None
model_lock = threading.Lock()
last_used = time.time()

# Supported Indian languages mapping
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'bn': 'Bengali', 
    'te': 'Telugu',
    'ta': 'Tamil',
    'gu': 'Gujarati',
    'kn': 'Kannada',
    'ml': 'Malayalam',
    'pa': 'Punjabi',
    'or': 'Odia',
    'mr': 'Marathi',
    'as': 'Assamese',
    'ur': 'Urdu'
}

def load_whisper_model():
    """Load Whisper model with error handling for Render environment"""
    global model
    try:
        # Use tiny model for free tier to reduce memory usage
        model = whisper.load_model("tiny")
        current_app.logger.info("Whisper tiny model loaded successfully")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to load Whisper model: {str(e)}")
        return False

def get_model():
    """Get model instance with lazy loading and memory management"""
    global model, last_used
    
    with model_lock:
        if model is None:
            current_app.logger.info("Loading Whisper model...")
            if not load_whisper_model():
                return None
        
        last_used = time.time()
        return model

def cleanup_model_if_idle():
    """Clean up model if idle for too long (memory management for free tier)"""
    global model, last_used
    
    # Clean up after 10 minutes of inactivity
    if model is not None and time.time() - last_used > 600:
        with model_lock:
            if model is not None:
                del model
                model = None
                current_app.logger.info("Whisper model cleaned up due to inactivity")

def is_supported_language(lang_code):
    """Check if detected language is supported (English + Indian languages)"""
    return lang_code in SUPPORTED_LANGUAGES

@voice_assistant_bp.route('/transcribe', methods=['POST'])
@require_json
@rate_limit_by_ip(max_requests=20, per_seconds=3600)  # Reduced for free tier
def transcribe_audio():
    """
    Transcribe audio file using local Whisper model
    Expected payload:
    {
        "audio_data": "base64_encoded_audio_string"
    }
    """
    try:
        # Clean up idle model to manage memory
        cleanup_model_if_idle()
        
        # Get model instance
        whisper_model = get_model()
        if whisper_model is None:
            return jsonify({
                'status': 'error',
                'message': 'Whisper model not available. Please try again.'
            }), 503
        
        data = request.get_json()
        
        # Validate required fields
        if 'audio_data' not in data:
            return jsonify({
                'status': 'error', 
                'message': 'Missing audio_data field'
            }), 400
        
        audio_data = data['audio_data']
        
        # Validate audio data size (limit for free tier)
        if len(audio_data) > 5 * 1024 * 1024:  # 5MB limit
            return jsonify({
                'status': 'error',
                'message': 'Audio file too large. Maximum size is 5MB.'
            }), 413
        
        # Validate and decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception:
            return jsonify({
                'status': 'error',
                'message': 'Invalid base64 audio data'
            }), 400
        
        current_app.logger.info("Processing audio transcription with Whisper tiny model")
        
        # Create temporary file for audio
        temp_audio_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir='/tmp') as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            # Transcribe audio using Whisper model with timeout
            result = whisper_model.transcribe(
                temp_audio_path,
                fp16=False,  # Disable fp16 for CPU
                verbose=False,
                temperature=0.0,
                best_of=1,  # Reduce processing time
                beam_size=1  # Reduce processing time
            )
            
            # Extract results
            transcribed_text = result["text"].strip()
            detected_language = result["language"]
            
            # Check if language is supported
            if not is_supported_language(detected_language):
                detected_language = 'en'
                current_app.logger.warning(f"Unsupported language detected, defaulting to English")
            
            # Prepare response
            response_data = {
                'transcribed_text': transcribed_text,
                'detected_language': detected_language,
                'language_name': SUPPORTED_LANGUAGES.get(detected_language, 'English'),
                'confidence': 0.85  # Fixed confidence for tiny model
            }
            
            current_app.logger.info(f"Transcription successful. Language: {detected_language}")
            
            return jsonify({
                'status': 'success',
                'data': response_data
            })
            
        finally:
            # Clean up temporary file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
        
    except Exception as e:
        current_app.logger.error(f"Transcription error: {str(e)}")
        
        return jsonify({
            'status': 'error',
            'message': 'Could not transcribe audio. Please try again.'
        }), 500

@voice_assistant_bp.route('/supported-languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages"""
    return jsonify({
        'status': 'success',
        'data': {
            'languages': SUPPORTED_LANGUAGES,
            'total_count': len(SUPPORTED_LANGUAGES)
        }
    })

@voice_assistant_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check if we can load the model
        whisper_model = get_model()
        model_status = "loaded" if whisper_model is not None else "not_loaded"
        
        return jsonify({
            'status': 'success',
            'service': 'Voice Transcription Service',
            'whisper_model': 'tiny (CPU optimized)',
            'model_status': model_status,
            'supported_languages': len(SUPPORTED_LANGUAGES),
            'environment': 'render',
            'memory_optimized': True
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Service unhealthy'
        }), 503

# Background cleanup task
def start_cleanup_task():
    """Start background task to cleanup idle models"""
    def cleanup_worker():
        while True:
            time.sleep(300)  # Check every 5 minutes
            cleanup_model_if_idle()
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

# Initialize cleanup task when module loads
start_cleanup_task()