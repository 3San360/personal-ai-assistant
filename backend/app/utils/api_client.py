"""
Generic API Client for handling HTTP requests with error handling and retries.
"""

import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class APIClient:
    """Generic async HTTP client with retry logic and error handling."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the API client.
        
        Args:
            timeout (int): Request timeout in seconds
            max_retries (int): Maximum number of retry attempts
            retry_delay (float): Delay between retries in seconds
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get(self, url: str, params: Dict[str, Any] = None, 
                  headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Perform GET request with retry logic.
        
        Args:
            url (str): Request URL
            params (Dict[str, Any]): Query parameters
            headers (Dict[str, str]): Request headers
            
        Returns:
            Dict[str, Any]: Response JSON data
            
        Raises:
            aiohttp.ClientError: For HTTP errors
            asyncio.TimeoutError: For timeout errors
        """
        return await self._request('GET', url, params=params, headers=headers)
    
    async def post(self, url: str, data: Dict[str, Any] = None, 
                   json_data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Perform POST request with retry logic.
        
        Args:
            url (str): Request URL
            data (Dict[str, Any]): Form data
            json_data (Dict[str, Any]): JSON data
            headers (Dict[str, str]): Request headers
            
        Returns:
            Dict[str, Any]: Response JSON data
        """
        return await self._request('POST', url, data=data, json=json_data, headers=headers)
    
    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Perform HTTP request with retry logic.
        
        Args:
            method (str): HTTP method
            url (str): Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Dict[str, Any]: Response JSON data
        """
        last_exception = None
        
        # Create session if not in context manager
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            should_close = True
        else:
            should_close = False
        
        try:
            for attempt in range(self.max_retries + 1):
                try:
                    start_time = time.time()
                    
                    async with self.session.request(method, url, **kwargs) as response:
                        response_time = time.time() - start_time
                        
                        logger.debug(f"{method} {url} - {response.status} ({response_time:.2f}s)")
                        
                        # Check for HTTP errors
                        if response.status >= 400:
                            error_text = await response.text()
                            logger.warning(f"HTTP {response.status} error for {url}: {error_text}")
                            
                            # Don't retry client errors (4xx), only server errors (5xx)
                            if response.status < 500 or attempt == self.max_retries:
                                try:
                                    error_json = await response.json()
                                    return error_json
                                except:
                                    return {"error": error_text, "status": response.status}
                        else:
                            # Successful response
                            try:
                                return await response.json()
                            except aiohttp.ContentTypeError:
                                # Not JSON response, return text
                                text = await response.text()
                                return {"text": text, "status": response.status}
                
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_exception = e
                    logger.warning(f"Request attempt {attempt + 1} failed for {url}: {str(e)}")
                    
                    # Don't wait after the last attempt
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                
                except Exception as e:
                    last_exception = e
                    logger.error(f"Unexpected error for {url}: {str(e)}")
                    break
            
            # All retries failed
            if last_exception:
                raise last_exception
            else:
                raise aiohttp.ClientError("Request failed after all retries")
        
        finally:
            if should_close and self.session:
                await self.session.close()
                self.session = None
    
    async def get_with_cache(self, url: str, params: Dict[str, Any] = None, 
                           cache_key: str = None, cache_ttl: int = 300) -> Dict[str, Any]:
        """
        Perform GET request with simple in-memory caching.
        
        Args:
            url (str): Request URL
            params (Dict[str, Any]): Query parameters
            cache_key (str): Cache key (auto-generated if None)
            cache_ttl (int): Cache TTL in seconds
            
        Returns:
            Dict[str, Any]: Response JSON data
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        # Generate cache key
        if not cache_key:
            cache_key = f"{url}_{hash(str(sorted((params or {}).items())))}"
        
        # Check cache
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry['timestamp'] < cache_ttl:
                logger.debug(f"Cache hit for {cache_key}")
                return cache_entry['data']
        
        # Make request
        data = await self.get(url, params=params)
        
        # Store in cache
        self._cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # Clean old cache entries (simple cleanup)
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry['timestamp'] > cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        
        logger.debug(f"Cache miss for {cache_key}, stored new data")
        return data
