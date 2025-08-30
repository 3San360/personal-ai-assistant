"""
Response models for the Personal AI Assistant API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class ChatResponse:
    """Standard chat response format."""
    message: str
    response_type: str = "text"  # text, voice, action
    confidence: float = 1.0
    actions_taken: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class WeatherResponse:
    """Weather API response format."""
    location: str
    current_temp: float
    feels_like: float
    humidity: int
    description: str
    icon: str
    forecast: List[Dict[str, Any]] = field(default_factory=list)
    units: str = "metric"

@dataclass
class NewsResponse:
    """News API response format."""
    articles: List[Dict[str, Any]]
    total_results: int
    category: str = "general"
    sources: List[str] = field(default_factory=list)

@dataclass
class CalendarResponse:
    """Calendar API response format."""
    events: List[Dict[str, Any]]
    action: str  # "list", "create", "update", "delete"
    success: bool = True
    message: str = ""

@dataclass
class VoiceResponse:
    """Voice processing response format."""
    text: str
    confidence: float
    language: str = "en"
    audio_duration: float = 0.0
    processing_time: float = 0.0

@dataclass
class ErrorResponse:
    """Standard error response format."""
    error: str
    error_code: str
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None
