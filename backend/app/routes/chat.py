"""
Chat routes for the Personal AI Assistant API.
"""

from flask import Blueprint, request, jsonify
import asyncio
import logging

from app.services import ConversationService
from app.utils.helpers import sanitize_input, generate_unique_id

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

# Initialize conversation service
conversation_service = ConversationService()

@chat_bp.route('/message', methods=['POST'])
def send_message():
    """
    Process a chat message from the user.
    
    Expected JSON payload:
    {
        "message": "User's message",
        "conversation_id": "optional conversation ID",
        "user_preferences": {
            "location": "user's location",
            "units": "metric or imperial",
            "language": "en"
        }
    }
    
    Returns:
        JSON response with assistant's reply
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract and validate message
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Sanitize input
        message = sanitize_input(message, max_length=1000)
        
        # Get optional parameters
        conversation_id = data.get('conversation_id')
        user_preferences = data.get('user_preferences', {})
        
        # Process message asynchronously
        response = asyncio.run(conversation_service.process_message(
            message=message,
            conversation_id=conversation_id,
            user_preferences=user_preferences
        ))
        
        if response.success:
            return jsonify({
                'success': True,
                'response': {
                    'message': response.data.message,
                    'response_type': response.data.response_type,
                    'confidence': response.data.confidence,
                    'actions_taken': response.data.actions_taken,
                    'suggestions': response.data.suggestions,
                    'timestamp': response.data.timestamp.isoformat()
                },
                'conversation_id': response.metadata.get('conversation_id'),
                'intent': response.metadata.get('intent'),
                'intent_confidence': response.metadata.get('confidence')
            })
        else:
            return jsonify({
                'success': False,
                'error': response.error
            }), 500
    
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@chat_bp.route('/conversation/<conversation_id>/history', methods=['GET'])
def get_conversation_history(conversation_id):
    """
    Get conversation message history.
    
    Args:
        conversation_id (str): Conversation ID
    
    Query parameters:
        limit (int): Maximum number of messages to return (default: 20)
    
    Returns:
        JSON response with conversation history
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        limit = max(1, min(limit, 100))  # Clamp between 1 and 100
        
        # Get conversation history
        messages = conversation_service.get_conversation_history(conversation_id, limit)
        
        # Format messages for response
        formatted_messages = []
        for message in messages:
            formatted_messages.append({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat(),
                'is_user': message.is_user,
                'message_type': message.message_type,
                'metadata': message.metadata
            })
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'messages': formatted_messages,
            'total_messages': len(formatted_messages)
        })
    
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get conversation history'
        }), 500

@chat_bp.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation_info(conversation_id):
    """
    Get conversation information and context.
    
    Args:
        conversation_id (str): Conversation ID
    
    Returns:
        JSON response with conversation information
    """
    try:
        conversation = conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'conversation': {
                'id': conversation.id,
                'created_at': conversation.created_at.isoformat(),
                'updated_at': conversation.updated_at.isoformat(),
                'message_count': len(conversation.messages),
                'context': conversation.context,
                'user_preferences': conversation.user_preferences
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting conversation info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get conversation information'
        }), 500

@chat_bp.route('/conversation/new', methods=['POST'])
def create_conversation():
    """
    Create a new conversation.
    
    Expected JSON payload:
    {
        "user_preferences": {
            "location": "user's location",
            "units": "metric or imperial",
            "language": "en"
        }
    }
    
    Returns:
        JSON response with new conversation ID
    """
    try:
        data = request.get_json() or {}
        user_preferences = data.get('user_preferences', {})
        
        # Create new conversation by processing an initial message
        response = asyncio.run(conversation_service.process_message(
            message="Hello",
            conversation_id=None,
            user_preferences=user_preferences
        ))
        
        if response.success:
            return jsonify({
                'success': True,
                'conversation_id': response.metadata.get('conversation_id'),
                'initial_response': {
                    'message': response.data.message,
                    'suggestions': response.data.suggestions
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': response.error
            }), 500
    
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create conversation'
        }), 500

@chat_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """
    Get general conversation suggestions.
    
    Returns:
        JSON response with suggested queries
    """
    try:
        suggestions = [
            {
                'text': "What's the weather like today?",
                'category': 'weather',
                'description': 'Get current weather information'
            },
            {
                'text': "Show me the latest news",
                'category': 'news',
                'description': 'Get current news headlines'
            },
            {
                'text': "What's on my calendar today?",
                'category': 'calendar',
                'description': 'View today\'s calendar events'
            },
            {
                'text': "Technology news",
                'category': 'news',
                'description': 'Get latest technology news'
            },
            {
                'text': "Weather forecast for this week",
                'category': 'weather',
                'description': 'Get weather forecast'
            },
            {
                'text': "Help - what can you do?",
                'category': 'help',
                'description': 'Learn about available features'
            }
        ]
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get suggestions'
        }), 500
