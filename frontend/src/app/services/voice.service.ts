import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError, from } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

import { environment } from '@environments/environment';
import { 
  VoiceResponse, 
  VoiceState, 
  VoiceSettings, 
  VoiceCapabilities,
  SpeechSynthesisSettings 
} from '@app/models';

// Extend Window interface for browser speech APIs
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

@Injectable({
  providedIn: 'root'
})
export class VoiceService {
  private readonly apiUrl = environment.apiUrl;
  
  // Voice state management
  private voiceStateSubject = new BehaviorSubject<VoiceState>({
    isRecording: false,
    isProcessing: false,
    isSupported: false
  });
  public voiceState$ = this.voiceStateSubject.asObservable();

  // Speech recognition instance
  private recognition: any = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];

  // Voice capabilities
  private capabilities: VoiceCapabilities = {
    speechRecognition: false,
    speechSynthesis: false,
    mediaRecorder: false,
    webAudio: false
  };

  constructor(private http: HttpClient) {
    this.initializeVoiceCapabilities();
    this.initializeSpeechRecognition();
  }

  /**
   * Initialize voice capabilities detection
   */
  private initializeVoiceCapabilities(): void {
    // Check Speech Recognition support
    this.capabilities.speechRecognition = !!(
      window.SpeechRecognition || window.webkitSpeechRecognition
    );

    // Check Speech Synthesis support
    this.capabilities.speechSynthesis = !!(
      window.speechSynthesis && window.SpeechSynthesisUtterance
    );

    // Check MediaRecorder support
    this.capabilities.mediaRecorder = !!(
      window.MediaRecorder && navigator.mediaDevices
    );

    // Check Web Audio API support
    this.capabilities.webAudio = !!(
      window.AudioContext || (window as any).webkitAudioContext
    );

    // Update voice state
    this.updateVoiceState({
      isSupported: this.capabilities.speechRecognition || this.capabilities.mediaRecorder
    });
  }

  /**
   * Initialize speech recognition
   */
  private initializeSpeechRecognition(): void {
    if (!this.capabilities.speechRecognition) {
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();

    // Configure speech recognition
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = environment.voice.defaultLanguage;
    this.recognition.maxAlternatives = 1;

    // Set up event handlers
    this.setupSpeechRecognitionEvents();
  }

  /**
   * Set up speech recognition event handlers
   */
  private setupSpeechRecognitionEvents(): void {
    if (!this.recognition) return;

    this.recognition.onstart = () => {
      console.log('Speech recognition started');
      this.updateVoiceState({ isRecording: true, error: undefined });
    };

    this.recognition.onresult = (event: any) => {
      const results = event.results;
      const lastResult = results[results.length - 1];
      
      if (lastResult.isFinal) {
        const transcript = lastResult[0].transcript;
        const confidence = lastResult[0].confidence;
        
        console.log('Speech recognition result:', transcript);
        this.handleSpeechResult(transcript, confidence);
      }
    };

    this.recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      this.updateVoiceState({ 
        isRecording: false, 
        isProcessing: false,
        error: `Speech recognition error: ${event.error}` 
      });
    };

    this.recognition.onend = () => {
      console.log('Speech recognition ended');
      this.updateVoiceState({ isRecording: false });
    };
  }

  /**
   * Start voice recording using browser speech recognition
   */
  startRecording(settings?: Partial<VoiceSettings>): Observable<VoiceResponse> {
    return new Observable(observer => {
      if (!this.capabilities.speechRecognition) {
        observer.error('Speech recognition not supported');
        return;
      }

      if (this.voiceStateSubject.value.isRecording) {
        observer.error('Already recording');
        return;
      }

      // Apply settings
      if (settings) {
        this.applySpeechSettings(settings);
      }

      // Set up result handler
      const originalOnResult = this.recognition.onresult;
      this.recognition.onresult = (event: any) => {
        originalOnResult(event);
        
        const results = event.results;
        const lastResult = results[results.length - 1];
        
        if (lastResult.isFinal) {
          const transcript = lastResult[0].transcript;
          const confidence = lastResult[0].confidence || 0.8;
          
          observer.next({
            text: transcript,
            confidence: confidence,
            language: this.recognition.lang,
            processingTime: 0
          });
          observer.complete();
        }
      };

      // Set up error handler
      const originalOnError = this.recognition.onerror;
      this.recognition.onerror = (event: any) => {
        originalOnError(event);
        observer.error(new Error(`Speech recognition error: ${event.error}`));
      };

      // Start recording
      try {
        this.recognition.start();
      } catch (error) {
        observer.error(error);
      }
    });
  }

  /**
   * Stop voice recording
   */
  stopRecording(): void {
    if (this.recognition && this.voiceStateSubject.value.isRecording) {
      this.recognition.stop();
    }
  }

  /**
   * Send audio to backend for processing
   */
  processAudioWithBackend(audioBlob: Blob, language: string = 'en-US'): Observable<VoiceResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');
    formData.append('language', language);

    return this.http.post<any>(`${this.apiUrl}/voice/speech-to-text`, formData).pipe(
      map(response => {
        if (response.success) {
          return {
            text: response.text,
            confidence: response.confidence,
            language: response.language,
            processingTime: response.processing_time
          };
        } else {
          throw new Error(response.error || 'Speech processing failed');
        }
      }),
      catchError(error => {
        console.error('Backend speech processing error:', error);
        return throwError(() => error);
      })
    );
  }

  /**
   * Convert text to speech using browser API
   */
  speakText(text: string, settings?: SpeechSynthesisSettings): Observable<void> {
    return new Observable(observer => {
      if (!this.capabilities.speechSynthesis) {
        observer.error('Speech synthesis not supported');
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);

      // Apply settings
      if (settings) {
        if (settings.voice) utterance.voice = settings.voice;
        if (settings.volume !== undefined) utterance.volume = settings.volume;
        if (settings.rate !== undefined) utterance.rate = settings.rate;
        if (settings.pitch !== undefined) utterance.pitch = settings.pitch;
        if (settings.language) utterance.lang = settings.language;
      }

      // Set up event handlers
      utterance.onstart = () => {
        console.log('Speech synthesis started');
      };

      utterance.onend = () => {
        console.log('Speech synthesis ended');
        observer.next();
        observer.complete();
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error);
        observer.error(new Error(`Speech synthesis error: ${event.error}`));
      };

      // Start speaking
      window.speechSynthesis.speak(utterance);
    });
  }

  /**
   * Get available voices
   */
  getAvailableVoices(): SpeechSynthesisVoice[] {
    if (!this.capabilities.speechSynthesis) {
      return [];
    }

    return window.speechSynthesis.getVoices();
  }

  /**
   * Process voice chat (record, transcribe, get response, speak)
   */
  processVoiceChat(conversationId?: string): Observable<{
    userText: string;
    assistantText: string;
    audioData?: string;
  }> {
    return new Observable(observer => {
      // First, record user speech
      this.startRecording().subscribe({
        next: (voiceResult) => {
          const userText = voiceResult.text;
          
          // Send to backend for voice chat processing
          const payload = {
            audio_data: '', // Would need actual audio data for backend processing
            conversation_id: conversationId
          };

          this.http.post<any>(`${this.apiUrl}/voice/voice-chat`, payload).subscribe({
            next: (response) => {
              if (response.success) {
                // Speak the response
                this.speakText(response.assistant_text).subscribe({
                  next: () => {
                    observer.next({
                      userText: response.user_text,
                      assistantText: response.assistant_text,
                      audioData: response.audio_data
                    });
                    observer.complete();
                  },
                  error: (error) => observer.error(error)
                });
              } else {
                observer.error(new Error(response.error));
              }
            },
            error: (error) => observer.error(error)
          });
        },
        error: (error) => observer.error(error)
      });
    });
  }

  /**
   * Check if voice features are supported
   */
  getCapabilities(): VoiceCapabilities {
    return { ...this.capabilities };
  }

  /**
   * Apply speech recognition settings
   */
  private applySpeechSettings(settings: Partial<VoiceSettings>): void {
    if (!this.recognition) return;

    if (settings.language) {
      this.recognition.lang = settings.language;
    }
    if (settings.continuous !== undefined) {
      this.recognition.continuous = settings.continuous;
    }
    if (settings.interimResults !== undefined) {
      this.recognition.interimResults = settings.interimResults;
    }
    if (settings.maxAlternatives !== undefined) {
      this.recognition.maxAlternatives = settings.maxAlternatives;
    }
  }

  /**
   * Handle speech recognition result
   */
  private handleSpeechResult(transcript: string, confidence: number): void {
    console.log('Speech result:', { transcript, confidence });
    // This can be overridden by specific implementations
  }

  /**
   * Update voice state
   */
  private updateVoiceState(updates: Partial<VoiceState>): void {
    const currentState = this.voiceStateSubject.value;
    this.voiceStateSubject.next({ ...currentState, ...updates });
  }

  /**
   * Get current voice state
   */
  get currentState(): VoiceState {
    return this.voiceStateSubject.value;
  }

  /**
   * Check if recording is in progress
   */
  get isRecording(): boolean {
    return this.voiceStateSubject.value.isRecording;
  }

  /**
   * Check if processing is in progress
   */
  get isProcessing(): boolean {
    return this.voiceStateSubject.value.isProcessing;
  }

  /**
   * Check if voice features are supported
   */
  get isSupported(): boolean {
    return this.voiceStateSubject.value.isSupported;
  }
}
