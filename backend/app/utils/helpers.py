"""
Utility helper functions for the Personal AI Assistant.
"""

import re
import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input by removing potentially harmful content.
    
    Args:
        text (str): Input text to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def generate_unique_id(prefix: str = "") -> str:
    """
    Generate a unique identifier.
    
    Args:
        prefix (str): Optional prefix for the ID
        
    Returns:
        str: Unique identifier
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(4)
    
    if prefix:
        return f"{prefix}_{timestamp}_{random_part}"
    else:
        return f"{timestamp}_{random_part}"

def hash_string(text: str, salt: str = "") -> str:
    """
    Create a hash of a string for comparison purposes.
    
    Args:
        text (str): Text to hash
        salt (str): Optional salt for the hash
        
    Returns:
        str: Hashed string
    """
    combined = f"{text}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()

def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    
    Args:
        dt (datetime): Datetime object
        format_string (str): Format string
        
    Returns:
        str: Formatted datetime string
    """
    if not isinstance(dt, datetime):
        return str(dt)
    
    return dt.strftime(format_string)

def parse_datetime(dt_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    
    Args:
        dt_string (str): Datetime string
        format_string (str): Expected format string
        
    Returns:
        Optional[datetime]: Parsed datetime or None if failed
    """
    try:
        return datetime.strptime(dt_string, format_string)
    except (ValueError, TypeError):
        logger.warning(f"Failed to parse datetime: {dt_string}")
        return None

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        suffix (str): Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not isinstance(text, str):
        return str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text (str): Text to search for URLs
        
    Returns:
        List[str]: List of found URLs
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def clean_text(text: str, remove_extra_spaces: bool = True, 
               remove_special_chars: bool = False) -> str:
    """
    Clean text by removing unwanted characters and formatting.
    
    Args:
        text (str): Text to clean
        remove_extra_spaces (bool): Whether to remove extra spaces
        remove_special_chars (bool): Whether to remove special characters
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove extra whitespace
    if remove_extra_spaces:
        text = ' '.join(text.split())
    
    # Remove special characters if requested
    if remove_special_chars:
        text = re.sub(r'[^\w\s]', '', text)
    
    return text.strip()

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
        
    Returns:
        bool: True if valid email format
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL format
    """
    url_pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(url_pattern, url))

def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get value from dictionary with default.
    
    Args:
        dictionary (Dict[str, Any]): Dictionary to search
        key (str): Key to look for
        default (Any): Default value if key not found
        
    Returns:
        Any: Value or default
    """
    return dictionary.get(key, default) if isinstance(dictionary, dict) else default

def convert_size_to_bytes(size_str: str) -> int:
    """
    Convert size string (e.g., "1MB", "500KB") to bytes.
    
    Args:
        size_str (str): Size string
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()
    
    if size_str.endswith('B'):
        size_str = size_str[:-1]
    
    multipliers = {
        'K': 1024,
        'M': 1024 ** 2,
        'G': 1024 ** 3,
        'T': 1024 ** 4
    }
    
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            try:
                number = float(size_str[:-1])
                return int(number * multiplier)
            except ValueError:
                break
    
    try:
        return int(float(size_str))
    except ValueError:
        return 0

def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human readable format.
    
    Args:
        bytes_size (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if bytes_size == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(bytes_size)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"

def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        str: Current timestamp
    """
    return datetime.now(timezone.utc).isoformat()

def rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate rate limit key for caching.
    
    Args:
        identifier (str): User/IP identifier
        action (str): Action being rate limited
        
    Returns:
        str: Rate limit key
    """
    return f"rate_limit:{action}:{hash_string(identifier)}"

def paginate_list(items: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items (List[Any]): Items to paginate
        page (int): Page number (1-based)
        per_page (int): Items per page
        
    Returns:
        Dict[str, Any]: Pagination result
    """
    if page < 1:
        page = 1
    
    if per_page < 1:
        per_page = 10
    
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    page_items = items[start_index:end_index]
    
    return {
        "items": page_items,
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts (int): Maximum retry attempts
        delay (float): Initial delay between retries
        backoff (float): Backoff multiplier for delay
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            # All attempts failed
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator
