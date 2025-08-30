"""
News Service for Personal AI Assistant.
Integrates with NewsAPI to provide latest news information.
"""

import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from app.config import Config
from app.models import NewsResponse, APIResponse
from app.utils.api_client import APIClient

logger = logging.getLogger(__name__)

class NewsService:
    """Service for handling news-related queries and API interactions."""
    
    def __init__(self):
        """Initialize the news service with NewsAPI configuration."""
        self.api_key = Config.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"
        self.client = APIClient()
        
        # News categories available in NewsAPI
        self.categories = [
            "business", "entertainment", "general", "health", 
            "science", "sports", "technology"
        ]
        
        if not self.api_key:
            logger.warning("NewsAPI key not configured")
    
    async def get_top_headlines(self, country: str = "us", category: str = None, 
                               page_size: int = 10) -> APIResponse:
        """
        Get top headlines from NewsAPI.
        
        Args:
            country (str): Country code (us, gb, fr, etc.)
            category (str): News category (business, entertainment, etc.)
            page_size (int): Number of articles to retrieve (max 100)
            
        Returns:
            APIResponse: Contains NewsResponse or error information
        """
        try:
            url = f"{self.base_url}/top-headlines"
            params = {
                "apiKey": self.api_key,
                "country": country,
                "pageSize": min(page_size, 100)
            }
            
            if category and category.lower() in self.categories:
                params["category"] = category.lower()
            
            response = await self.client.get(url, params=params)
            
            if response.get("status") != "ok":
                return APIResponse(
                    success=False,
                    error=f"News API error: {response.get('message', 'Unknown error')}"
                )
            
            news_data = self._parse_news_response(response, category or "general")
            
            return APIResponse(
                success=True,
                data=news_data,
                metadata={
                    "country": country,
                    "category": category,
                    "page_size": page_size
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting top headlines: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to get news headlines: {str(e)}"
            )
    
    async def search_news(self, query: str, sort_by: str = "publishedAt", 
                         page_size: int = 10, language: str = "en") -> APIResponse:
        """
        Search for news articles based on keywords.
        
        Args:
            query (str): Search query
            sort_by (str): Sort order (publishedAt, relevancy, popularity)
            page_size (int): Number of articles to retrieve
            language (str): Language code (en, es, fr, etc.)
            
        Returns:
            APIResponse: Contains NewsResponse or error information
        """
        try:
            url = f"{self.base_url}/everything"
            
            # Calculate date range (last 30 days)
            to_date = datetime.now()
            from_date = to_date - timedelta(days=30)
            
            params = {
                "apiKey": self.api_key,
                "q": query,
                "sortBy": sort_by,
                "pageSize": min(page_size, 100),
                "language": language,
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d")
            }
            
            response = await self.client.get(url, params=params)
            
            if response.get("status") != "ok":
                return APIResponse(
                    success=False,
                    error=f"News search error: {response.get('message', 'Unknown error')}"
                )
            
            news_data = self._parse_news_response(response, "search")
            
            return APIResponse(
                success=True,
                data=news_data,
                metadata={
                    "query": query,
                    "sort_by": sort_by,
                    "language": language,
                    "page_size": page_size
                }
            )
            
        except Exception as e:
            logger.error(f"Error searching news: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to search news: {str(e)}"
            )
    
    async def get_news_by_sources(self, sources: List[str], page_size: int = 10) -> APIResponse:
        """
        Get news from specific sources.
        
        Args:
            sources (List[str]): List of news source IDs
            page_size (int): Number of articles to retrieve
            
        Returns:
            APIResponse: Contains NewsResponse or error information
        """
        try:
            url = f"{self.base_url}/everything"
            params = {
                "apiKey": self.api_key,
                "sources": ",".join(sources[:20]),  # Max 20 sources
                "pageSize": min(page_size, 100),
                "sortBy": "publishedAt"
            }
            
            response = await self.client.get(url, params=params)
            
            if response.get("status") != "ok":
                return APIResponse(
                    success=False,
                    error=f"News sources error: {response.get('message', 'Unknown error')}"
                )
            
            news_data = self._parse_news_response(response, "sources")
            
            return APIResponse(
                success=True,
                data=news_data,
                metadata={
                    "sources": sources,
                    "page_size": page_size
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting news by sources: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to get news by sources: {str(e)}"
            )
    
    async def get_available_sources(self, category: str = None, country: str = None) -> APIResponse:
        """
        Get available news sources.
        
        Args:
            category (str): Filter by category
            country (str): Filter by country
            
        Returns:
            APIResponse: Contains list of news sources
        """
        try:
            url = f"{self.base_url}/sources"
            params = {"apiKey": self.api_key}
            
            if category and category.lower() in self.categories:
                params["category"] = category.lower()
            
            if country:
                params["country"] = country.lower()
            
            response = await self.client.get(url, params=params)
            
            if response.get("status") != "ok":
                return APIResponse(
                    success=False,
                    error=f"Sources API error: {response.get('message', 'Unknown error')}"
                )
            
            sources = response.get("sources", [])
            
            return APIResponse(
                success=True,
                data=sources,
                metadata={
                    "category": category,
                    "country": country,
                    "total_sources": len(sources)
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting news sources: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to get news sources: {str(e)}"
            )
    
    def _parse_news_response(self, data: Dict, category: str) -> NewsResponse:
        """
        Parse news API response into NewsResponse object.
        
        Args:
            data (Dict): Raw API response
            category (str): News category
            
        Returns:
            NewsResponse: Parsed news data
        """
        articles = data.get("articles", [])
        
        # Clean and format articles
        formatted_articles = []
        sources = set()
        
        for article in articles:
            # Skip articles with missing essential data
            if not article.get("title") or not article.get("url"):
                continue
            
            # Format publication date
            published_at = article.get("publishedAt")
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M UTC")
                except:
                    formatted_date = published_at
            else:
                formatted_date = "Unknown"
            
            # Extract source name
            source = article.get("source", {})
            source_name = source.get("name", "Unknown Source")
            sources.add(source_name)
            
            formatted_article = {
                "title": article.get("title", "").strip(),
                "description": article.get("description", "").strip() if article.get("description") else "",
                "url": article.get("url", ""),
                "urlToImage": article.get("urlToImage"),
                "publishedAt": formatted_date,
                "source": source_name,
                "author": article.get("author", "Unknown")
            }
            
            formatted_articles.append(formatted_article)
        
        return NewsResponse(
            articles=formatted_articles,
            total_results=data.get("totalResults", len(formatted_articles)),
            category=category,
            sources=list(sources)
        )
    
    def format_news_message(self, news_data: NewsResponse, max_articles: int = 5) -> str:
        """
        Format news data into a human-readable message.
        
        Args:
            news_data (NewsResponse): News information
            max_articles (int): Maximum number of articles to include
            
        Returns:
            str: Formatted news message
        """
        if not news_data.articles:
            return "📰 No news articles found for your query."
        
        category_emoji = {
            "business": "💼",
            "entertainment": "🎭",
            "health": "🏥",
            "science": "🔬",
            "sports": "⚽",
            "technology": "💻",
            "general": "📰"
        }
        
        emoji = category_emoji.get(news_data.category, "📰")
        
        message = f"{emoji} Latest {news_data.category.title()} News:\n\n"
        
        for i, article in enumerate(news_data.articles[:max_articles]):
            message += f"📄 **{article['title']}**\n"
            
            if article.get("description"):
                # Truncate description if too long
                description = article["description"]
                if len(description) > 150:
                    description = description[:150] + "..."
                message += f"   {description}\n"
            
            message += f"   📅 {article['publishedAt']} | 📰 {article['source']}\n"
            message += f"   🔗 {article['url']}\n\n"
        
        if len(news_data.articles) > max_articles:
            remaining = len(news_data.articles) - max_articles
            message += f"... and {remaining} more articles available."
        
        return message.strip()
    
    def detect_news_category(self, query: str) -> Optional[str]:
        """
        Detect news category from user query.
        
        Args:
            query (str): User query
            
        Returns:
            Optional[str]: Detected category or None
        """
        query_lower = query.lower()
        
        category_keywords = {
            "business": ["business", "economy", "finance", "stock", "market", "trade", "company"],
            "entertainment": ["entertainment", "celebrity", "movie", "music", "tv", "show", "actor"],
            "health": ["health", "medical", "doctor", "hospital", "medicine", "disease", "virus"],
            "science": ["science", "research", "study", "discovery", "space", "technology", "innovation"],
            "sports": ["sports", "football", "basketball", "soccer", "baseball", "game", "team"],
            "technology": ["technology", "tech", "computer", "software", "app", "digital", "ai", "artificial intelligence"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return None
    
    def get_news_intent_keywords(self) -> List[str]:
        """
        Get keywords that indicate news-related queries.
        
        Returns:
            List[str]: News intent keywords
        """
        return [
            "news", "headlines", "latest", "breaking", "article", "report", "story",
            "what's happening", "current events", "today's news", "updates"
        ]
