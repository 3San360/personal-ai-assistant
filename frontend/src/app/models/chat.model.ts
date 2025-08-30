/**
 * Chat message interface for the Personal AI Assistant
 */
export interface ChatMessage {
  id: string;
  content: string;
  timestamp: Date;
  isUser: boolean;
  messageType: 'text' | 'voice' | 'image';
  metadata?: Record<string, any>;
}

/**
 * Chat response from the assistant
 */
export interface ChatResponse {
  message: string;
  responseType: 'text' | 'voice' | 'action' | 'weather' | 'news' | 'calendar' | 'error' | 'greeting' | 'help';
  confidence: number;
  actionsTaken: string[];
  suggestions: string[];
  timestamp: Date;
}

/**
 * Conversation context and metadata
 */
export interface Conversation {
  id: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  context: Record<string, any>;
  userPreferences: UserPreferences;
}

/**
 * User preferences for personalization
 */
export interface UserPreferences {
  location?: string;
  units?: 'metric' | 'imperial';
  language?: string;
  voiceEnabled?: boolean;
  notifications?: boolean;
  theme?: 'light' | 'dark' | 'auto';
}

/**
 * API response wrapper
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  metadata?: Record<string, any>;
}

/**
 * Voice recording state
 */
export interface VoiceState {
  isRecording: boolean;
  isProcessing: boolean;
  isSupported: boolean;
  error?: string;
}

/**
 * Chat suggestion item
 */
export interface ChatSuggestion {
  text: string;
  category: 'weather' | 'news' | 'calendar' | 'general' | 'help';
  description?: string;
}
