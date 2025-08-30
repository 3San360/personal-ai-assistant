"""
Voice Service for Personal AI Assistant.
Handles speech recognition and text-to-speech functionality.
"""

import speech_recognition as sr
import pyttsx3
import threading
import tempfile
import os
import wave
import asyncio
from typing import Optional, Dict, Any
import logging

from app.config import Config
from app.models import VoiceResponse, APIResponse

logger = logging.getLogger(__name__)

class VoiceService:
    """Service for handling voice input and output operations."""
    
    def __init__(self):
        """Initialize the voice service with speech recognition and TTS engines."""
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.tts_engine = None
        
        # Initialize microphone
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Microphone initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing microphone: {str(e)}")
        
        # Initialize TTS engine
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            self.tts_engine.setProperty('rate', Config.VOICE_RATE)
            self.tts_engine.setProperty('volume', Config.VOICE_VOLUME)
            
            # Try to set a better voice if available
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {str(e)}")
    
    async def speech_to_text(self, audio_data: bytes = None, language: str = "en-US") -> APIResponse:
        """
        Convert speech to text using speech recognition.
        
        Args:
            audio_data (bytes): Audio data bytes (if None, will record from microphone)
            language (str): Language code for recognition
            
        Returns:
            APIResponse: Contains VoiceResponse or error information
        """
        if not self.recognizer:
            return APIResponse(
                success=False,
                error="Speech recognition not available"
            )
        
        try:
            import time
            start_time = time.time()
            
            # Get audio source
            if audio_data:
                # Process provided audio data
                audio_source = self._bytes_to_audio_source(audio_data)
            else:
                # Record from microphone
                if not self.microphone:
                    return APIResponse(
                        success=False,
                        error="Microphone not available"
                    )
                
                with self.microphone as source:
                    logger.info("Listening for speech...")
                    # Listen for audio with timeout
                    audio_source = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
            
            # Perform speech recognition
            try:
                # Try Google Speech Recognition first
                text = self.recognizer.recognize_google(audio_source, language=language)
                confidence = 0.9  # Google API doesn't provide confidence score
                
            except sr.RequestError:
                # Fallback to offline recognition
                try:
                    text = self.recognizer.recognize_sphinx(audio_source)
                    confidence = 0.7  # Lower confidence for offline recognition
                except sr.RequestError:
                    return APIResponse(
                        success=False,
                        error="Speech recognition service unavailable"
                    )
            
            processing_time = time.time() - start_time
            
            voice_data = VoiceResponse(
                text=text,
                confidence=confidence,
                language=language,
                processing_time=processing_time
            )
            
            return APIResponse(
                success=True,
                data=voice_data,
                metadata={
                    "recognition_engine": "google" if confidence > 0.8 else "sphinx",
                    "audio_duration": getattr(audio_source, 'duration_seconds', 0)
                }
            )
            
        except sr.UnknownValueError:
            return APIResponse(
                success=False,
                error="Could not understand the audio"
            )
        except sr.WaitTimeoutError:
            return APIResponse(
                success=False,
                error="Listening timeout - no speech detected"
            )
        except Exception as e:
            logger.error(f"Error in speech recognition: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Speech recognition failed: {str(e)}"
            )
    
    async def text_to_speech(self, text: str, save_to_file: bool = False) -> APIResponse:
        """
        Convert text to speech using TTS engine.
        
        Args:
            text (str): Text to convert to speech
            save_to_file (bool): Whether to save audio to file
            
        Returns:
            APIResponse: Contains file path if saved, or success status
        """
        if not self.tts_engine:
            return APIResponse(
                success=False,
                error="Text-to-speech engine not available"
            )
        
        try:
            if save_to_file:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                temp_file.close()
                
                # Configure TTS to save to file
                self.tts_engine.save_to_file(text, temp_file.name)
                self.tts_engine.runAndWait()
                
                return APIResponse(
                    success=True,
                    data={"file_path": temp_file.name, "text": text},
                    metadata={
                        "audio_format": "wav",
                        "text_length": len(text)
                    }
                )
            else:
                # Speak directly
                self._speak_text_async(text)
                
                return APIResponse(
                    success=True,
                    data={"text": text, "spoken": True},
                    metadata={
                        "text_length": len(text),
                        "estimated_duration": len(text) * 0.1  # Rough estimate
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Text-to-speech failed: {str(e)}"
            )
    
    def _speak_text_async(self, text: str):
        """
        Speak text asynchronously to avoid blocking.
        
        Args:
            text (str): Text to speak
        """
        def speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                logger.error(f"Error speaking text: {str(e)}")
        
        # Run TTS in separate thread
        thread = threading.Thread(target=speak)
        thread.daemon = True
        thread.start()
    
    def _bytes_to_audio_source(self, audio_bytes: bytes) -> sr.AudioData:
        """
        Convert audio bytes to AudioData object for speech recognition.
        
        Args:
            audio_bytes (bytes): Raw audio data
            
        Returns:
            sr.AudioData: Audio data object for recognition
        """
        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(audio_bytes)
        temp_file.close()
        
        try:
            # Read audio file
            with sr.AudioFile(temp_file.name) as source:
                audio_data = self.recognizer.record(source)
            
            return audio_data
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file.name)
            except:
                pass
    
    async def record_audio(self, duration: int = 5) -> APIResponse:
        """
        Record audio from microphone for specified duration.
        
        Args:
            duration (int): Recording duration in seconds
            
        Returns:
            APIResponse: Contains audio data or error information
        """
        if not self.microphone:
            return APIResponse(
                success=False,
                error="Microphone not available"
            )
        
        try:
            with self.microphone as source:
                logger.info(f"Recording audio for {duration} seconds...")
                # Record audio
                audio_data = self.recognizer.listen(source, timeout=1, phrase_time_limit=duration)
                
                # Convert to bytes
                audio_bytes = audio_data.get_wav_data()
                
                return APIResponse(
                    success=True,
                    data={
                        "audio_bytes": audio_bytes,
                        "duration": duration,
                        "sample_rate": audio_data.sample_rate,
                        "sample_width": audio_data.sample_width
                    },
                    metadata={
                        "format": "wav",
                        "channels": 1,
                        "recording_duration": duration
                    }
                )
                
        except Exception as e:
            logger.error(f"Error recording audio: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Audio recording failed: {str(e)}"
            )
    
    def is_microphone_available(self) -> bool:
        """
        Check if microphone is available for recording.
        
        Returns:
            bool: True if microphone is available
        """
        return self.microphone is not None
    
    def is_tts_available(self) -> bool:
        """
        Check if text-to-speech is available.
        
        Returns:
            bool: True if TTS is available
        """
        return self.tts_engine is not None
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available TTS voices.
        
        Returns:
            List[Dict[str, Any]]: Available voice information
        """
        if not self.tts_engine:
            return []
        
        try:
            voices = self.tts_engine.getProperty('voices')
            voice_list = []
            
            for voice in voices or []:
                voice_info = {
                    "id": voice.id,
                    "name": voice.name,
                    "languages": getattr(voice, 'languages', []),
                    "gender": getattr(voice, 'gender', 'unknown'),
                    "age": getattr(voice, 'age', 'unknown')
                }
                voice_list.append(voice_info)
            
            return voice_list
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the TTS voice by ID.
        
        Args:
            voice_id (str): Voice ID to set
            
        Returns:
            bool: True if voice was set successfully
        """
        if not self.tts_engine:
            return False
        
        try:
            self.tts_engine.setProperty('voice', voice_id)
            return True
        except Exception as e:
            logger.error(f"Error setting voice: {str(e)}")
            return False
    
    def set_speech_rate(self, rate: int) -> bool:
        """
        Set the TTS speech rate.
        
        Args:
            rate (int): Speech rate (words per minute)
            
        Returns:
            bool: True if rate was set successfully
        """
        if not self.tts_engine:
            return False
        
        try:
            self.tts_engine.setProperty('rate', rate)
            return True
        except Exception as e:
            logger.error(f"Error setting speech rate: {str(e)}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Set the TTS volume.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if volume was set successfully
        """
        if not self.tts_engine:
            return False
        
        try:
            volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
            self.tts_engine.setProperty('volume', volume)
            return True
        except Exception as e:
            logger.error(f"Error setting volume: {str(e)}")
            return False
