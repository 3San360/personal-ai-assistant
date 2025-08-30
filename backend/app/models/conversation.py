"""
Data models for the Personal AI Assistant.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

@dataclass
class Message:
    """Represents a single message in a conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    is_user: bool = True
    message_type: str = "text"  # "text", "voice", "image"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Conversation:
    """Represents a conversation session with context memory."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, content: str, is_user: bool = True, message_type: str = "text", metadata: Dict[str, Any] = None):
        """
        Add a new message to the conversation.
        
        Args:
            content (str): Message content
            is_user (bool): Whether the message is from the user
            message_type (str): Type of message (text, voice, image)
            metadata (dict): Additional message metadata
        """
        if metadata is None:
            metadata = {}
            
        message = Message(
            content=content,
            is_user=is_user,
            message_type=message_type,
            metadata=metadata
        )
        
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Keep only last 50 messages to manage memory
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
    
    def get_recent_context(self, num_messages: int = 5) -> List[Message]:
        """
        Get recent messages for context.
        
        Args:
            num_messages (int): Number of recent messages to return
            
        Returns:
            List[Message]: Recent messages
        """
        return self.messages[-num_messages:] if self.messages else []
    
    def update_context(self, key: str, value: Any):
        """
        Update conversation context.
        
        Args:
            key (str): Context key
            value (Any): Context value
        """
        self.context[key] = value
        self.updated_at = datetime.now()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get context value.
        
        Args:
            key (str): Context key
            default (Any): Default value if key not found
            
        Returns:
            Any: Context value or default
        """
        return self.context.get(key, default)

@dataclass
class UserIntent:
    """Represents detected user intent from a message."""
    intent: str  # weather, news, calendar, general
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIResponse:
    """Standardized API response format."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
