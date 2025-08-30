"""
Voice routes for the Personal AI Assistant API.
"""

from flask import Blueprint, request, jsonify, send_file
import asyncio
import base64
import tempfile
import os
import logging

from app.services import VoiceService, ConversationService
from app.utils.helpers import sanitize_input

logger = logging.getLogger(__name__)
voice_bp = Blueprint('voice', __name__)

# Initialize services
voice_service = VoiceService()
conversation_service = ConversationService()

@voice_bp.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """
    Convert speech audio to text.
    
    Expected request:
    - Content-Type: application/json with base64 encoded audio
    OR
    - Content-Type: multipart/form-data with audio file
    
    JSON payload (if using base64):
    {
        "audio_data": "base64 encoded audio data",
        "language": "en-US"  # optional
    }
    
    Returns:
        JSON response with transcribed text
    """
    try:
        audio_data = None
        language = "en-US"
        
        # Handle different content types
        if request.content_type and 'application/json' in request.content_type:
            # JSON with base64 audio
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            audio_base64 = data.get('audio_data')
            if not audio_base64:
                return jsonify({'error': 'audio_data is required'}), 400
            
            try:
                audio_data = base64.b64decode(audio_base64)
            except Exception as e:
                return jsonify({'error': f'Invalid base64 audio data: {str(e)}'}), 400
            
            language = data.get('language', 'en-US')
        
        elif request.content_type and 'multipart/form-data' in request.content_type:
            # File upload
            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400
            
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({'error': 'No audio file selected'}), 400
            
            audio_data = audio_file.read()
            language = request.form.get('language', 'en-US')
        
        else:
            return jsonify({'error': 'Unsupported content type. Use application/json or multipart/form-data'}), 400
        
        # Check if voice service is available
        if not voice_service.is_microphone_available():
            return jsonify({
                'error': 'Speech recognition service not available'
            }), 503
        
        # Convert speech to text
        response = asyncio.run(voice_service.speech_to_text(audio_data, language))
        
        if response.success:
            return jsonify({
                'success': True,
                'text': response.data.text,
                'confidence': response.data.confidence,
                'language': response.data.language,
                'processing_time': response.data.processing_time
            })
        else:
            return jsonify({
                'success': False,
                'error': response.error
            }), 400
    
    except Exception as e:
        logger.error(f"Error in speech to text: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Speech recognition failed'
        }), 500

@voice_bp.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """
    Convert text to speech audio.
    
    Expected JSON payload:
    {
        "text": "Text to convert to speech",
        "save_to_file": false,  # optional, default false
        "voice_id": "voice_identifier"  # optional
    }
    
    Returns:
        JSON response with success status or audio file
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Sanitize text
        text = sanitize_input(text, max_length=1000)
        
        save_to_file = data.get('save_to_file', False)
        voice_id = data.get('voice_id')
        
        # Check if TTS service is available
        if not voice_service.is_tts_available():
            return jsonify({
                'error': 'Text-to-speech service not available'
            }), 503
        
        # Set voice if specified
        if voice_id:
            voice_service.set_voice(voice_id)
        
        # Convert text to speech
        response = asyncio.run(voice_service.text_to_speech(text, save_to_file))
        
        if response.success:
            if save_to_file and 'file_path' in response.data:
                # Return audio file
                file_path = response.data['file_path']
                try:
                    return send_file(
                        file_path,
                        as_attachment=True,
                        download_name='speech.wav',
                        mimetype='audio/wav'
                    )
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(file_path)
                    except:
                        pass
            else:
                # Return success status
                return jsonify({
                    'success': True,
                    'message': 'Speech synthesis started',
                    'text': response.data['text']
                })
        else:
            return jsonify({
                'success': False,
                'error': response.error
            }), 400
    
    except Exception as e:
        logger.error(f"Error in text to speech: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Text-to-speech conversion failed'
        }), 500

@voice_bp.route('/voice-chat', methods=['POST'])
def voice_chat():
    """
    Process voice input and return voice response.
    Combines speech-to-text, chat processing, and text-to-speech.
    
    Expected request similar to speech-to-text endpoint.
    
    Returns:
        JSON response with chat response and optional audio
    """
    try:
        audio_data = None
        language = "en-US"
        conversation_id = None
        
        # Handle different content types
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            audio_base64 = data.get('audio_data')
            if not audio_base64:
                return jsonify({'error': 'audio_data is required'}), 400
            
            try:
                audio_data = base64.b64decode(audio_base64)
            except Exception as e:
                return jsonify({'error': f'Invalid base64 audio data: {str(e)}'}), 400
            
            language = data.get('language', 'en-US')
            conversation_id = data.get('conversation_id')
        
        elif request.content_type and 'multipart/form-data' in request.content_type:
            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400
            
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({'error': 'No audio file selected'}), 400
            
            audio_data = audio_file.read()
            language = request.form.get('language', 'en-US')
            conversation_id = request.form.get('conversation_id')
        
        else:
            return jsonify({'error': 'Unsupported content type'}), 400
        
        # Check services availability
        if not voice_service.is_microphone_available() or not voice_service.is_tts_available():
            return jsonify({
                'error': 'Voice services not available'
            }), 503
        
        # Step 1: Convert speech to text
        stt_response = asyncio.run(voice_service.speech_to_text(audio_data, language))
        
        if not stt_response.success:
            return jsonify({
                'success': False,
                'error': f'Speech recognition failed: {stt_response.error}'
            }), 400
        
        user_message = stt_response.data.text
        
        # Step 2: Process chat message
        chat_response = asyncio.run(conversation_service.process_message(
            message=user_message,
            conversation_id=conversation_id
        ))
        
        if not chat_response.success:
            return jsonify({
                'success': False,
                'error': f'Chat processing failed: {chat_response.error}'
            }), 500
        
        assistant_message = chat_response.data.message
        
        # Step 3: Convert response to speech
        tts_response = asyncio.run(voice_service.text_to_speech(assistant_message, save_to_file=True))
        
        response_data = {
            'success': True,
            'user_text': user_message,
            'assistant_text': assistant_message,
            'response_type': chat_response.data.response_type,
            'confidence': chat_response.data.confidence,
            'conversation_id': chat_response.metadata.get('conversation_id'),
            'suggestions': chat_response.data.suggestions,
            'speech_confidence': stt_response.data.confidence
        }
        
        if tts_response.success and 'file_path' in tts_response.data:
            # Encode audio file as base64
            try:
                with open(tts_response.data['file_path'], 'rb') as audio_file:
                    audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')
                    response_data['audio_data'] = audio_base64
                    response_data['audio_format'] = 'wav'
            except Exception as e:
                logger.warning(f"Failed to encode audio file: {str(e)}")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tts_response.data['file_path'])
                except:
                    pass
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in voice chat: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Voice chat processing failed'
        }), 500

@voice_bp.route('/record', methods=['POST'])
def record_audio():
    """
    Record audio from microphone for specified duration.
    
    Expected JSON payload:
    {
        "duration": 5  # recording duration in seconds
    }
    
    Returns:
        JSON response with recorded audio data
    """
    try:
        data = request.get_json() or {}
        duration = data.get('duration', 5)
        duration = max(1, min(duration, 30))  # Clamp between 1 and 30 seconds
        
        if not voice_service.is_microphone_available():
            return jsonify({
                'error': 'Microphone not available'
            }), 503
        
        # Record audio
        response = asyncio.run(voice_service.record_audio(duration))
        
        if response.success:
            # Encode audio as base64
            audio_base64 = base64.b64encode(response.data['audio_bytes']).decode('utf-8')
            
            return jsonify({
                'success': True,
                'audio_data': audio_base64,
                'duration': response.data['duration'],
                'sample_rate': response.data['sample_rate'],
                'format': response.metadata['format']
            })
        else:
            return jsonify({
                'success': False,
                'error': response.error
            }), 400
    
    except Exception as e:
        logger.error(f"Error recording audio: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Audio recording failed'
        }), 500

@voice_bp.route('/voices', methods=['GET'])
def get_available_voices():
    """
    Get list of available TTS voices.
    
    Returns:
        JSON response with available voices
    """
    try:
        voices = voice_service.get_available_voices()
        
        return jsonify({
            'success': True,
            'voices': voices,
            'total_voices': len(voices)
        })
    
    except Exception as e:
        logger.error(f"Error getting voices: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get available voices'
        }), 500

@voice_bp.route('/status', methods=['GET'])
def voice_service_status():
    """
    Get voice service status.
    
    Returns:
        JSON response with service availability
    """
    try:
        return jsonify({
            'success': True,
            'microphone_available': voice_service.is_microphone_available(),
            'tts_available': voice_service.is_tts_available(),
            'voice_count': len(voice_service.get_available_voices())
        })
    
    except Exception as e:
        logger.error(f"Error getting voice service status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get voice service status'
        }), 500
