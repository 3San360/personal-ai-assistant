/**
 * Voice service interfaces and types
 */

export interface VoiceResponse {
  text: string;
  confidence: number;
  language: string;
  processingTime?: number;
}

export interface VoiceSettings {
  language: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
}

export interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

export interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
  length: number;
}

export interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

export interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

export interface SpeechSynthesisSettings {
  voice?: SpeechSynthesisVoice;
  volume?: number;
  rate?: number;
  pitch?: number;
  language?: string;
}

export interface VoiceCapabilities {
  speechRecognition: boolean;
  speechSynthesis: boolean;
  mediaRecorder: boolean;
  webAudio: boolean;
}
