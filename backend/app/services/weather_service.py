"""
Weather Service for Personal AI Assistant.
Integrates with OpenWeatherMap API to provide weather information.
"""

import requests
import asyncio
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging

from app.config import Config
from app.models import WeatherResponse, APIResponse
from app.utils.api_client import APIClient

logger = logging.getLogger(__name__)

class WeatherService:
    """Service for handling weather-related queries and API interactions."""
    
    def __init__(self):
        """Initialize the weather service with OpenWeatherMap API configuration."""
        self.api_key = Config.OPENWEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geo_url = "http://api.openweathermap.org/geo/1.0"
        self.client = APIClient()
        
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
    
    async def get_current_weather(self, location: str, units: str = "metric") -> APIResponse:
        """
        Get current weather for a specific location.
        
        Args:
            location (str): City name or "lat,lon" coordinates
            units (str): Temperature units (metric, imperial, kelvin)
            
        Returns:
            APIResponse: Contains WeatherResponse or error information
        """
        try:
            # First, get coordinates for the location
            coordinates = await self._get_coordinates(location)
            if not coordinates:
                return APIResponse(
                    success=False,
                    error=f"Location '{location}' not found"
                )
            
            lat, lon, display_name = coordinates
            
            # Get current weather
            url = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": units
            }
            
            response = await self.client.get(url, params=params)
            
            if response.get("cod") != 200:
                return APIResponse(
                    success=False,
                    error=f"Weather API error: {response.get('message', 'Unknown error')}"
                )
            
            weather_data = self._parse_current_weather(response, display_name, units)
            
            return APIResponse(
                success=True,
                data=weather_data,
                metadata={"units": units, "coordinates": {"lat": lat, "lon": lon}}
            )
            
        except Exception as e:
            logger.error(f"Error getting current weather: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to get weather information: {str(e)}"
            )
    
    async def get_weather_forecast(self, location: str, days: int = 5, units: str = "metric") -> APIResponse:
        """
        Get weather forecast for a specific location.
        
        Args:
            location (str): City name or "lat,lon" coordinates
            days (int): Number of days for forecast (1-5)
            units (str): Temperature units (metric, imperial, kelvin)
            
        Returns:
            APIResponse: Contains WeatherResponse with forecast or error information
        """
        try:
            coordinates = await self._get_coordinates(location)
            if not coordinates:
                return APIResponse(
                    success=False,
                    error=f"Location '{location}' not found"
                )
            
            lat, lon, display_name = coordinates
            
            # Get forecast
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": units,
                "cnt": min(days * 8, 40)  # API returns 3-hour intervals, max 40 calls
            }
            
            response = await self.client.get(url, params=params)
            
            if response.get("cod") != "200":
                return APIResponse(
                    success=False,
                    error=f"Forecast API error: {response.get('message', 'Unknown error')}"
                )
            
            weather_data = self._parse_forecast_weather(response, display_name, units, days)
            
            return APIResponse(
                success=True,
                data=weather_data,
                metadata={"units": units, "days": days, "coordinates": {"lat": lat, "lon": lon}}
            )
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to get weather forecast: {str(e)}"
            )
    
    async def _get_coordinates(self, location: str) -> Optional[Tuple[float, float, str]]:
        """
        Get coordinates for a location using geocoding API.
        
        Args:
            location (str): Location name
            
        Returns:
            Tuple[float, float, str]: (latitude, longitude, display_name) or None
        """
        try:
            # Check if location is already in lat,lon format
            if "," in location:
                parts = location.split(",")
                if len(parts) == 2:
                    try:
                        lat, lon = float(parts[0].strip()), float(parts[1].strip())
                        return lat, lon, f"{lat:.2f}, {lon:.2f}"
                    except ValueError:
                        pass
            
            # Use geocoding API
            url = f"{self.geo_url}/direct"
            params = {
                "q": location,
                "limit": 1,
                "appid": self.api_key
            }
            
            response = await self.client.get(url, params=params)
            
            if response and len(response) > 0:
                result = response[0]
                return (
                    result["lat"],
                    result["lon"],
                    f"{result['name']}, {result.get('country', '')}"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting coordinates for {location}: {str(e)}")
            return None
    
    def _parse_current_weather(self, data: Dict, location: str, units: str) -> WeatherResponse:
        """
        Parse current weather API response into WeatherResponse object.
        
        Args:
            data (Dict): Raw API response
            location (str): Location display name
            units (str): Temperature units
            
        Returns:
            WeatherResponse: Parsed weather data
        """
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        
        return WeatherResponse(
            location=location,
            current_temp=main.get("temp", 0),
            feels_like=main.get("feels_like", 0),
            humidity=main.get("humidity", 0),
            description=weather.get("description", "").title(),
            icon=weather.get("icon", ""),
            units=units
        )
    
    def _parse_forecast_weather(self, data: Dict, location: str, units: str, days: int) -> WeatherResponse:
        """
        Parse forecast weather API response into WeatherResponse object.
        
        Args:
            data (Dict): Raw API response
            location (str): Location display name
            units (str): Temperature units
            days (int): Number of forecast days
            
        Returns:
            WeatherResponse: Parsed weather data with forecast
        """
        forecasts = data.get("list", [])
        
        # Group forecasts by day and get daily summaries
        daily_forecasts = []
        current_day = None
        daily_temps = []
        daily_weather = None
        
        for forecast in forecasts[:days * 8]:  # Limit to requested days
            dt = datetime.fromtimestamp(forecast["dt"], tz=timezone.utc)
            day = dt.date()
            
            if current_day != day:
                # Save previous day if exists
                if current_day and daily_temps:
                    daily_forecasts.append({
                        "date": current_day.isoformat(),
                        "temp_min": min(daily_temps),
                        "temp_max": max(daily_temps),
                        "description": daily_weather.get("description", "").title(),
                        "icon": daily_weather.get("icon", "")
                    })
                
                # Start new day
                current_day = day
                daily_temps = []
                daily_weather = forecast.get("weather", [{}])[0]
            
            daily_temps.append(forecast["main"]["temp"])
        
        # Add last day
        if current_day and daily_temps:
            daily_forecasts.append({
                "date": current_day.isoformat(),
                "temp_min": min(daily_temps),
                "temp_max": max(daily_temps),
                "description": daily_weather.get("description", "").title(),
                "icon": daily_weather.get("icon", "")
            })
        
        # Use first forecast item for current weather
        current = forecasts[0] if forecasts else {}
        main = current.get("main", {})
        weather = current.get("weather", [{}])[0]
        
        return WeatherResponse(
            location=location,
            current_temp=main.get("temp", 0),
            feels_like=main.get("feels_like", 0),
            humidity=main.get("humidity", 0),
            description=weather.get("description", "").title(),
            icon=weather.get("icon", ""),
            forecast=daily_forecasts,
            units=units
        )
    
    def format_weather_message(self, weather_data: WeatherResponse) -> str:
        """
        Format weather data into a human-readable message.
        
        Args:
            weather_data (WeatherResponse): Weather information
            
        Returns:
            str: Formatted weather message
        """
        units_symbol = "°C" if weather_data.units == "metric" else "°F"
        
        message = f"🌤️ Weather in {weather_data.location}:\n"
        message += f"Currently {weather_data.current_temp:.1f}{units_symbol} "
        message += f"(feels like {weather_data.feels_like:.1f}{units_symbol})\n"
        message += f"{weather_data.description}\n"
        message += f"Humidity: {weather_data.humidity}%"
        
        if weather_data.forecast:
            message += "\n\n📅 Forecast:\n"
            for day_forecast in weather_data.forecast[:5]:  # Show max 5 days
                date = datetime.fromisoformat(day_forecast["date"]).strftime("%A, %B %d")
                message += f"{date}: {day_forecast['temp_min']:.1f}-{day_forecast['temp_max']:.1f}{units_symbol} "
                message += f"- {day_forecast['description']}\n"
        
        return message.strip()
    
    def get_weather_intent_keywords(self) -> List[str]:
        """
        Get keywords that indicate weather-related queries.
        
        Returns:
            List[str]: Weather intent keywords
        """
        return [
            "weather", "temperature", "temp", "forecast", "rain", "snow", "sunny", 
            "cloudy", "humidity", "wind", "storm", "hot", "cold", "warm", "cool",
            "degrees", "celsius", "fahrenheit", "precipitation", "climate"
        ]
