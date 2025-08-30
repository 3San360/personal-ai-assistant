/* Production configuration */
export const environment = {
  production: true,
  apiUrl: 'https://your-api-domain.com/api/v1', // Update with your production API URL
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
    speechTimeout: 10000,
    silenceTimeout: 2000,
    maxRecordingTime: 30000
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
