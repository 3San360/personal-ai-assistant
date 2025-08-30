"""
Conversation Service for Personal AI Assistant.
Manages conversation context, memory, and intent detection.
"""

import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

from app.models import Conversation, Message, UserIntent, ChatResponse, APIResponse
from app.services.weather_service import WeatherService
from app.services.news_service import NewsService
from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing conversations, context, and intent detection."""
    
    def __init__(self):
        """Initialize the conversation service with external services."""
        self.conversations: Dict[str, Conversation] = {}
        self.weather_service = WeatherService()
        self.news_service = NewsService()
        self.calendar_service = CalendarService()
        
        # Intent keywords mapping
        self.intent_keywords = {
            "weather": self.weather_service.get_weather_intent_keywords(),
            "news": self.news_service.get_news_intent_keywords(),
            "calendar": self.calendar_service.get_calendar_intent_keywords(),
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "goodbye": ["bye", "goodbye", "see you", "farewell", "exit", "quit"],
            "help": ["help", "what can you do", "commands", "assistance", "support"],
            "thanks": ["thank you", "thanks", "appreciate", "grateful"]
        }
    
    async def process_message(self, message: str, conversation_id: str = None, 
                             user_preferences: Dict[str, Any] = None) -> APIResponse:
        """
        Process a user message and generate an appropriate response.
        
        Args:
            message (str): User's message
            conversation_id (str): Conversation ID (creates new if None)
            user_preferences (Dict[str, Any]): User preferences
            
        Returns:
            APIResponse: Contains ChatResponse or error information
        """
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(conversation_id, user_preferences)
            
            # Add user message to conversation
            conversation.add_message(message, is_user=True)
            
            # Detect intent
            intent = self._detect_intent(message, conversation)
            
            # Process based on intent
            response = await self._handle_intent(intent, message, conversation)
            
            # Add assistant response to conversation
            conversation.add_message(response.message, is_user=False)
            
            # Update conversation metadata
            conversation.update_context("last_intent", intent.intent)
            conversation.update_context("last_message_time", datetime.now())
            
            return APIResponse(
                success=True,
                data=response,
                metadata={
                    "conversation_id": conversation.id,
                    "intent": intent.intent,
                    "confidence": intent.confidence
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to process message: {str(e)}"
            )
    
    def _get_or_create_conversation(self, conversation_id: str = None, 
                                   user_preferences: Dict[str, Any] = None) -> Conversation:
        """
        Get existing conversation or create a new one.
        
        Args:
            conversation_id (str): Conversation ID
            user_preferences (Dict[str, Any]): User preferences
            
        Returns:
            Conversation: Conversation object
        """
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        
        # Create new conversation
        conversation = Conversation(user_preferences=user_preferences or {})
        self.conversations[conversation.id] = conversation
        
        # Clean up old conversations (keep last 10)
        if len(self.conversations) > 10:
            oldest_conversations = sorted(
                self.conversations.items(),
                key=lambda x: x[1].updated_at
            )[:-10]
            
            for old_id, _ in oldest_conversations:
                del self.conversations[old_id]
        
        return conversation
    
    def _detect_intent(self, message: str, conversation: Conversation) -> UserIntent:
        """
        Detect user intent from message content and conversation context.
        
        Args:
            message (str): User's message
            conversation (Conversation): Current conversation
            
        Returns:
            UserIntent: Detected intent with confidence and entities
        """
        message_lower = message.lower()
        
        # Check for explicit intent patterns
        intent_scores = {}
        
        # Calculate scores for each intent
        for intent_name, keywords in self.intent_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                # Normalize score by number of keywords
                normalized_score = score / len(keywords)
                intent_scores[intent_name] = {
                    "score": normalized_score,
                    "keywords": matched_keywords
                }
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k]["score"])
            confidence = min(intent_scores[primary_intent]["score"] * 2, 1.0)  # Scale to 0-1
            
            # Extract entities based on intent
            entities = self._extract_entities(message, primary_intent, conversation)
            
            return UserIntent(
                intent=primary_intent,
                confidence=confidence,
                entities=entities,
                parameters={"matched_keywords": intent_scores[primary_intent]["keywords"]}
            )
        
        # Default to general conversation
        return UserIntent(
            intent="general",
            confidence=0.5,
            entities={},
            parameters={}
        )
    
    def _extract_entities(self, message: str, intent: str, conversation: Conversation) -> Dict[str, Any]:
        """
        Extract relevant entities from message based on intent.
        
        Args:
            message (str): User's message
            intent (str): Detected intent
            conversation (Conversation): Current conversation
            
        Returns:
            Dict[str, Any]: Extracted entities
        """
        entities = {}
        message_lower = message.lower()
        
        if intent == "weather":
            # Extract location
            location = self._extract_location(message)
            if location:
                entities["location"] = location
            
            # Extract time reference
            if any(word in message_lower for word in ["tomorrow", "today", "forecast", "week"]):
                entities["time_reference"] = "forecast"
            else:
                entities["time_reference"] = "current"
        
        elif intent == "news":
            # Extract news category
            category = self.news_service.detect_news_category(message)
            if category:
                entities["category"] = category
            
            # Extract search terms
            news_terms = self._extract_news_terms(message)
            if news_terms:
                entities["search_terms"] = news_terms
        
        elif intent == "calendar":
            # Extract calendar action
            if any(word in message_lower for word in ["schedule", "create", "add", "book"]):
                entities["action"] = "create"
            elif any(word in message_lower for word in ["list", "show", "what's", "upcoming"]):
                entities["action"] = "list"
            else:
                entities["action"] = "list"  # Default
            
            # Extract time references
            time_entities = self._extract_time_entities(message)
            entities.update(time_entities)
        
        return entities
    
    def _extract_location(self, message: str) -> Optional[str]:
        """
        Extract location from message.
        
        Args:
            message (str): User's message
            
        Returns:
            Optional[str]: Extracted location
        """
        # Simple location extraction patterns
        location_patterns = [
            r"in\s+([A-Za-z\s,]+?)(?:\s|$|[?.!])",
            r"for\s+([A-Za-z\s,]+?)(?:\s|$|[?.!])",
            r"at\s+([A-Za-z\s,]+?)(?:\s|$|[?.!])",
            r"weather\s+([A-Za-z\s,]+?)(?:\s|$|[?.!])"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Filter out common words that aren't locations
                if location.lower() not in ["today", "tomorrow", "now", "there", "here"]:
                    return location
        
        return None
    
    def _extract_news_terms(self, message: str) -> Optional[str]:
        """
        Extract search terms for news from message.
        
        Args:
            message (str): User's message
            
        Returns:
            Optional[str]: Extracted search terms
        """
        # Extract terms after "about", "on", "regarding"
        search_patterns = [
            r"about\s+(.+?)(?:\s|$)",
            r"on\s+(.+?)(?:\s|$)",
            r"regarding\s+(.+?)(?:\s|$)",
            r"news\s+(.+?)(?:\s|$)"
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                terms = match.group(1).strip()
                # Clean up common words
                terms = re.sub(r'\b(news|latest|today|yesterday)\b', '', terms, flags=re.IGNORECASE)
                terms = terms.strip()
                if terms:
                    return terms
        
        return None
    
    def _extract_time_entities(self, message: str) -> Dict[str, Any]:
        """
        Extract time-related entities from message.
        
        Args:
            message (str): User's message
            
        Returns:
            Dict[str, Any]: Time entities
        """
        entities = {}
        message_lower = message.lower()
        
        # Time references
        if "today" in message_lower:
            entities["date_reference"] = "today"
        elif "tomorrow" in message_lower:
            entities["date_reference"] = "tomorrow"
        elif "next week" in message_lower:
            entities["date_reference"] = "next_week"
        elif "this week" in message_lower:
            entities["date_reference"] = "this_week"
        
        # Extract specific times
        time_pattern = r'(\d{1,2}):(\d{2})\s*(am|pm)?'
        match = re.search(time_pattern, message_lower)
        if match:
            entities["time"] = match.group(0)
        
        return entities
    
    async def _handle_intent(self, intent: UserIntent, message: str, 
                           conversation: Conversation) -> ChatResponse:
        """
        Handle user intent and generate appropriate response.
        
        Args:
            intent (UserIntent): Detected user intent
            message (str): Original user message
            conversation (Conversation): Current conversation
            
        Returns:
            ChatResponse: Generated response
        """
        if intent.intent == "weather":
            return await self._handle_weather_intent(intent, message, conversation)
        elif intent.intent == "news":
            return await self._handle_news_intent(intent, message, conversation)
        elif intent.intent == "calendar":
            return await self._handle_calendar_intent(intent, message, conversation)
        elif intent.intent == "greeting":
            return self._handle_greeting_intent(intent, message, conversation)
        elif intent.intent == "goodbye":
            return self._handle_goodbye_intent(intent, message, conversation)
        elif intent.intent == "help":
            return self._handle_help_intent(intent, message, conversation)
        elif intent.intent == "thanks":
            return self._handle_thanks_intent(intent, message, conversation)
        else:
            return self._handle_general_intent(intent, message, conversation)
    
    async def _handle_weather_intent(self, intent: UserIntent, message: str, 
                                   conversation: Conversation) -> ChatResponse:
        """Handle weather-related queries."""
        location = intent.entities.get("location", "current location")
        time_ref = intent.entities.get("time_reference", "current")
        
        if time_ref == "forecast":
            result = await self.weather_service.get_weather_forecast(location)
        else:
            result = await self.weather_service.get_current_weather(location)
        
        if result.success:
            formatted_message = self.weather_service.format_weather_message(result.data)
            return ChatResponse(
                message=formatted_message,
                response_type="weather",
                confidence=intent.confidence,
                actions_taken=[f"Retrieved weather for {location}"]
            )
        else:
            return ChatResponse(
                message=f"Sorry, I couldn't get weather information. {result.error}",
                response_type="error",
                confidence=intent.confidence
            )
    
    async def _handle_news_intent(self, intent: UserIntent, message: str, 
                                conversation: Conversation) -> ChatResponse:
        """Handle news-related queries."""
        category = intent.entities.get("category")
        search_terms = intent.entities.get("search_terms")
        
        if search_terms:
            result = await self.news_service.search_news(search_terms)
        else:
            result = await self.news_service.get_top_headlines(category=category)
        
        if result.success:
            formatted_message = self.news_service.format_news_message(result.data)
            action = f"Retrieved {category or 'general'} news"
            if search_terms:
                action = f"Searched news for '{search_terms}'"
            
            return ChatResponse(
                message=formatted_message,
                response_type="news",
                confidence=intent.confidence,
                actions_taken=[action]
            )
        else:
            return ChatResponse(
                message=f"Sorry, I couldn't get news information. {result.error}",
                response_type="error",
                confidence=intent.confidence
            )
    
    async def _handle_calendar_intent(self, intent: UserIntent, message: str, 
                                    conversation: Conversation) -> ChatResponse:
        """Handle calendar-related queries."""
        action = intent.entities.get("action", "list")
        
        if action == "list":
            result = await self.calendar_service.list_events()
        else:
            # For create action, we'd need more sophisticated parsing
            return ChatResponse(
                message="I can help you view your calendar events. To create events, please use specific commands like 'Schedule a meeting tomorrow at 2 PM'.",
                response_type="calendar",
                confidence=intent.confidence,
                suggestions=["What's on my calendar today?", "Show upcoming events"]
            )
        
        if result.success:
            formatted_message = self.calendar_service.format_calendar_message(result.data)
            return ChatResponse(
                message=formatted_message,
                response_type="calendar",
                confidence=intent.confidence,
                actions_taken=["Retrieved calendar events"]
            )
        else:
            return ChatResponse(
                message=f"Sorry, I couldn't access your calendar. {result.error}",
                response_type="error",
                confidence=intent.confidence
            )
    
    def _handle_greeting_intent(self, intent: UserIntent, message: str, 
                              conversation: Conversation) -> ChatResponse:
        """Handle greeting messages."""
        greetings = [
            "Hello! I'm your personal AI assistant. How can I help you today?",
            "Hi there! I can help you with weather, news, calendar, and more. What would you like to know?",
            "Good day! I'm here to assist you with various tasks. What can I do for you?"
        ]
        
        # Choose greeting based on time of day
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning! How can I assist you today?"
        elif hour < 17:
            greeting = "Good afternoon! What can I help you with?"
        else:
            greeting = "Good evening! How may I be of service?"
        
        return ChatResponse(
            message=greeting,
            response_type="greeting",
            confidence=intent.confidence,
            suggestions=[
                "What's the weather like?",
                "Show me the latest news",
                "What's on my calendar today?",
                "What can you do?"
            ]
        )
    
    def _handle_goodbye_intent(self, intent: UserIntent, message: str, 
                             conversation: Conversation) -> ChatResponse:
        """Handle goodbye messages."""
        farewells = [
            "Goodbye! Have a great day!",
            "See you later! Feel free to ask me anything anytime.",
            "Farewell! I'm always here when you need assistance."
        ]
        
        import random
        farewell = random.choice(farewells)
        
        return ChatResponse(
            message=farewell,
            response_type="goodbye",
            confidence=intent.confidence
        )
    
    def _handle_help_intent(self, intent: UserIntent, message: str, 
                          conversation: Conversation) -> ChatResponse:
        """Handle help requests."""
        help_message = """🤖 **Personal AI Assistant - Help**

I can help you with:

🌤️ **Weather**: 
   • "What's the weather in New York?"
   • "Will it rain today?"
   • "Weather forecast for this week"

📰 **News**: 
   • "Show me the latest news"
   • "Technology news"
   • "News about climate change"

📅 **Calendar**: 
   • "What's on my calendar today?"
   • "Show upcoming events"
   • "Schedule a meeting" (basic support)

🎤 **Voice Commands**: 
   • Click the microphone button to speak
   • I can respond with voice too!

Just ask me naturally - I understand conversational language!"""
        
        return ChatResponse(
            message=help_message,
            response_type="help",
            confidence=intent.confidence,
            suggestions=[
                "Weather in London",
                "Latest tech news",
                "My calendar today"
            ]
        )
    
    def _handle_thanks_intent(self, intent: UserIntent, message: str, 
                            conversation: Conversation) -> ChatResponse:
        """Handle thank you messages."""
        responses = [
            "You're welcome! Happy to help!",
            "My pleasure! Is there anything else you need?",
            "Glad I could help! Feel free to ask me anything else."
        ]
        
        import random
        response = random.choice(responses)
        
        return ChatResponse(
            message=response,
            response_type="thanks",
            confidence=intent.confidence,
            suggestions=[
                "What else can you do?",
                "Show me the weather",
                "Latest news please"
            ]
        )
    
    def _handle_general_intent(self, intent: UserIntent, message: str, 
                             conversation: Conversation) -> ChatResponse:
        """Handle general conversation."""
        general_responses = [
            "I understand you're trying to communicate with me, but I'm not sure exactly what you need. Could you be more specific?",
            "I'm here to help with weather, news, and calendar information. What would you like to know?",
            "I didn't quite understand that. You can ask me about the weather, latest news, or your calendar events."
        ]
        
        import random
        response = random.choice(general_responses)
        
        return ChatResponse(
            message=response,
            response_type="general",
            confidence=0.3,
            suggestions=[
                "Help - show me what you can do",
                "What's the weather like?",
                "Show me today's news",
                "What's on my calendar?"
            ]
        )
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID.
        
        Args:
            conversation_id (str): Conversation ID
            
        Returns:
            Optional[Conversation]: Conversation object or None
        """
        return self.conversations.get(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 20) -> List[Message]:
        """
        Get conversation message history.
        
        Args:
            conversation_id (str): Conversation ID
            limit (int): Maximum number of messages to return
            
        Returns:
            List[Message]: Message history
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return []
        
        return conversation.messages[-limit:] if conversation.messages else []
