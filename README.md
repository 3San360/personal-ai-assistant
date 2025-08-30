# AI Assistant Platform

A comprehensive full-stack Personal AI Assistant application featuring voice interaction, API integrations, and a modern Angular frontend. The assistant can handle weather inquiries, news updates, calendar management, and general conversations with both text and voice input/output capabilities.

## Features

- **Text Chat Interface**: Clean, modern chat interface
- **Voice Input/Output**: Speech recognition and text-to-speech capabilities
- **Weather Integration**: Get current weather and forecasts using OpenWeatherMap API
- **News Integration**: Fetch latest news using NewsAPI
- **Calendar Integration**: Google Calendar scheduling and event management
- **Conversation Memory**: Maintains context across conversations
- **Modular Architecture**: Clean, reusable code with proper separation of concerns
- **Async API Calls**: Non-blocking API requests with robust error handling
- **Security**: Best practices for API key management

## Tech Stack

### Backend
- **Python 3.8+**
- **Flask**: Web framework
- **Flask-CORS**: Cross-origin resource sharing
- **Requests**: HTTP library for API calls
- **Python-dotenv**: Environment variable management
- **Google API Client**: Google Calendar integration
- **SpeechRecognition**: Voice input processing
- **pyttsx3**: Text-to-speech output

### Frontend
- **Angular 15+**
- **Angular Material**: UI components
- **Web Speech API**: Browser-based speech recognition
- **RxJS**: Reactive programming for API calls

## Project Structure

```
project-one/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Flask application entry point
│   │   ├── config.py            # Configuration management
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py  # Conversation memory models
│   │   │   └── response.py      # Response models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── weather_service.py    # Weather API integration
│   │   │   ├── news_service.py       # News API integration
│   │   │   ├── calendar_service.py   # Google Calendar integration
│   │   │   ├── voice_service.py      # Voice processing
│   │   │   └── conversation_service.py # Context management
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── api_client.py    # Generic API client
│   │   │   └── helpers.py       # Utility functions
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py          # Chat endpoints
│   │       ├── voice.py         # Voice endpoints
│   │       └── health.py        # Health check endpoints
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── chat/
│   │   │   │   ├── voice-control/
│   │   │   │   └── settings/
│   │   │   ├── services/
│   │   │   │   ├── chat.service.ts
│   │   │   │   ├── voice.service.ts
│   │   │   │   └── config.service.ts
│   │   │   ├── models/
│   │   │   └── app.module.ts
│   │   ├── assets/
│   │   └── environments/
│   ├── angular.json
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   ├── API.md
│   └── SETUP.md
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- Google Cloud Console account (for Calendar API)
- OpenWeatherMap API key
- NewsAPI key

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```
   OPENWEATHER_API_KEY=your_openweather_api_key
   NEWS_API_KEY=your_news_api_key
   GOOGLE_CALENDAR_CREDENTIALS_FILE=path_to_google_credentials.json
   FLASK_SECRET_KEY=your_secret_key
   ```

5. **Run the backend**:
   ```bash
   python run.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   Edit `src/environments/environment.ts` with your backend URL

4. **Run the frontend**:
   ```bash
   ng serve
   ```

### API Keys Setup

#### OpenWeatherMap API
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key
4. Add to `.env` file

#### NewsAPI
1. Visit [NewsAPI](https://newsapi.org/)
2. Register for a free account
3. Get your API key
4. Add to `.env` file

#### Google Calendar API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create credentials (OAuth 2.0 or Service Account)
5. Download credentials JSON file
6. Add file path to `.env`

## Usage

### Text Chat
1. Open the application in your browser
2. Type your questions in the chat interface
3. Ask about weather: "What's the weather like in New York?"
4. Get news: "Show me the latest tech news"
5. Schedule events: "Schedule a meeting for tomorrow at 2 PM"

### Voice Commands
1. Click the microphone button
2. Speak your command
3. The assistant will respond with both text and voice

### Supported Commands

#### Weather
- "What's the weather in [city]?"
- "Will it rain today?"
- "Weather forecast for this week"

#### News
- "Show me the latest news"
- "Technology news"
- "News about [topic]"

#### Calendar
- "Schedule a meeting"
- "What's on my calendar today?"
- "Add an event for [date/time]"

#### General
- "Hello" / "Hi"
- "Help" / "What can you do?"
- "Thank you"

## Development

### Adding New Services

1. Create a new service file in `backend/app/services/`
2. Implement the service interface
3. Add route handlers in `backend/app/routes/`
4. Update frontend service if needed

### Testing

Run backend tests:
```bash
cd backend
python -m pytest tests/
```

Run frontend tests:
```bash
cd frontend
ng test
```

## Security Considerations

- API keys are stored in environment variables
- CORS is configured for production
- Input validation on all endpoints
- Rate limiting implemented
- Error messages don't expose sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open an issue on GitHub or contact the development team.
