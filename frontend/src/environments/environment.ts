/* Application configuration */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:5000/api/v1',
  appName: 'Personal AI Assistant',
  version: '1.0.0',
  
  // Feature flags
  features: {
    voiceInput: true,
    voiceOutput: true,
    weatherIntegration: true,
    newsIntegration: true,
    calendarIntegration: true,
    conversationHistory: true
  },
  
  // Voice settings
  voice: {
    defaultLanguage: 'en-US',
    speechTimeout: 10000, // 10 seconds
    silenceTimeout: 2000, // 2 seconds
    maxRecordingTime: 30000 // 30 seconds
  },
  
  // Chat settings
  chat: {
    maxMessageLength: 1000,
    typingIndicatorDelay: 500,
    messageAnimationDuration: 300
  },
  
  // UI settings
  ui: {
    theme: 'default',
    showTimestamps: true,
    enableAnimations: true,
    compactMode: false
  }
};
