"""
Calendar Service for Personal AI Assistant.
Integrates with Google Calendar API to manage events and scheduling.
"""

import os
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import Config
from app.models import CalendarResponse, APIResponse

logger = logging.getLogger(__name__)

class CalendarService:
    """Service for handling calendar-related operations with Google Calendar API."""
    
    # Google Calendar API scopes
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        """Initialize the calendar service with Google Calendar API configuration."""
        self.credentials_file = Config.GOOGLE_CALENDAR_CREDENTIALS_FILE
        self.token_file = Config.GOOGLE_CALENDAR_TOKEN_FILE
        self.service = None
        
        if not self.credentials_file:
            logger.warning("Google Calendar credentials file not configured")
        else:
            self._authenticate()
    
    def _authenticate(self):
        """
        Authenticate with Google Calendar API using OAuth2.
        """
        try:
            creds = None
            
            # Load existing token if available
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refresh expired credentials
                    creds.refresh(Request())
                else:
                    # Run OAuth flow for new credentials
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build the Calendar service
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar service authenticated successfully")
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {str(e)}")
            self.service = None
    
    async def list_events(self, calendar_id: str = 'primary', max_results: int = 10, 
                         days_ahead: int = 7) -> APIResponse:
        """
        List upcoming events from Google Calendar.
        
        Args:
            calendar_id (str): Calendar ID (default: 'primary')
            max_results (int): Maximum number of events to return
            days_ahead (int): Number of days ahead to look for events
            
        Returns:
            APIResponse: Contains CalendarResponse or error information
        """
        if not self.service:
            return APIResponse(
                success=False,
                error="Google Calendar service not authenticated"
            )
        
        try:
            # Calculate time range
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events
            formatted_events = []
            for event in events:
                formatted_event = self._format_event(event)
                formatted_events.append(formatted_event)
            
            calendar_data = CalendarResponse(
                events=formatted_events,
                action="list",
                success=True,
                message=f"Found {len(formatted_events)} upcoming events"
            )
            
            return APIResponse(
                success=True,
                data=calendar_data,
                metadata={
                    "calendar_id": calendar_id,
                    "days_ahead": days_ahead,
                    "total_events": len(formatted_events)
                }
            )
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Calendar API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error listing events: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to list events: {str(e)}"
            )
    
    async def create_event(self, title: str, start_time: datetime, end_time: datetime,
                          description: str = "", location: str = "", 
                          calendar_id: str = 'primary') -> APIResponse:
        """
        Create a new event in Google Calendar.
        
        Args:
            title (str): Event title
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            description (str): Event description
            location (str): Event location
            calendar_id (str): Calendar ID (default: 'primary')
            
        Returns:
            APIResponse: Contains CalendarResponse or error information
        """
        if not self.service:
            return APIResponse(
                success=False,
                error="Google Calendar service not authenticated"
            )
        
        try:
            # Create event object
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if location:
                event['location'] = location
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            formatted_event = self._format_event(created_event)
            
            calendar_data = CalendarResponse(
                events=[formatted_event],
                action="create",
                success=True,
                message=f"Event '{title}' created successfully"
            )
            
            return APIResponse(
                success=True,
                data=calendar_data,
                metadata={
                    "event_id": created_event.get('id'),
                    "calendar_id": calendar_id
                }
            )
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Calendar API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to create event: {str(e)}"
            )
    
    async def update_event(self, event_id: str, updates: Dict[str, Any],
                          calendar_id: str = 'primary') -> APIResponse:
        """
        Update an existing event in Google Calendar.
        
        Args:
            event_id (str): Event ID to update
            updates (Dict[str, Any]): Updates to apply
            calendar_id (str): Calendar ID (default: 'primary')
            
        Returns:
            APIResponse: Contains CalendarResponse or error information
        """
        if not self.service:
            return APIResponse(
                success=False,
                error="Google Calendar service not authenticated"
            )
        
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Apply updates
            if 'title' in updates:
                event['summary'] = updates['title']
            if 'description' in updates:
                event['description'] = updates['description']
            if 'location' in updates:
                event['location'] = updates['location']
            if 'start_time' in updates:
                event['start']['dateTime'] = updates['start_time'].isoformat()
            if 'end_time' in updates:
                event['end']['dateTime'] = updates['end_time'].isoformat()
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            formatted_event = self._format_event(updated_event)
            
            calendar_data = CalendarResponse(
                events=[formatted_event],
                action="update",
                success=True,
                message=f"Event updated successfully"
            )
            
            return APIResponse(
                success=True,
                data=calendar_data,
                metadata={
                    "event_id": event_id,
                    "calendar_id": calendar_id
                }
            )
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Calendar API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error updating event: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to update event: {str(e)}"
            )
    
    async def delete_event(self, event_id: str, calendar_id: str = 'primary') -> APIResponse:
        """
        Delete an event from Google Calendar.
        
        Args:
            event_id (str): Event ID to delete
            calendar_id (str): Calendar ID (default: 'primary')
            
        Returns:
            APIResponse: Contains CalendarResponse or error information
        """
        if not self.service:
            return APIResponse(
                success=False,
                error="Google Calendar service not authenticated"
            )
        
        try:
            # Delete the event
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            calendar_data = CalendarResponse(
                events=[],
                action="delete",
                success=True,
                message=f"Event deleted successfully"
            )
            
            return APIResponse(
                success=True,
                data=calendar_data,
                metadata={
                    "event_id": event_id,
                    "calendar_id": calendar_id
                }
            )
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Calendar API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return APIResponse(
                success=False,
                error=f"Failed to delete event: {str(e)}"
            )
    
    def _format_event(self, event: Dict) -> Dict[str, Any]:
        """
        Format a Google Calendar event for consistent output.
        
        Args:
            event (Dict): Raw Google Calendar event
            
        Returns:
            Dict[str, Any]: Formatted event data
        """
        # Handle start and end times
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Extract datetime or date
        start_time = start.get('dateTime', start.get('date'))
        end_time = end.get('dateTime', end.get('date'))
        
        # Format dates
        if start_time:
            try:
                if 'T' in start_time:  # DateTime
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    start_formatted = start_dt.strftime('%Y-%m-%d %H:%M')
                else:  # Date only
                    start_formatted = start_time
            except:
                start_formatted = start_time
        else:
            start_formatted = "Unknown"
        
        if end_time:
            try:
                if 'T' in end_time:  # DateTime
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    end_formatted = end_dt.strftime('%Y-%m-%d %H:%M')
                else:  # Date only
                    end_formatted = end_time
            except:
                end_formatted = end_time
        else:
            end_formatted = "Unknown"
        
        return {
            'id': event.get('id', ''),
            'title': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start_time': start_formatted,
            'end_time': end_formatted,
            'status': event.get('status', 'confirmed'),
            'html_link': event.get('htmlLink', ''),
            'created': event.get('created', ''),
            'updated': event.get('updated', '')
        }
    
    def format_calendar_message(self, calendar_data: CalendarResponse) -> str:
        """
        Format calendar data into a human-readable message.
        
        Args:
            calendar_data (CalendarResponse): Calendar information
            
        Returns:
            str: Formatted calendar message
        """
        if calendar_data.action == "list":
            if not calendar_data.events:
                return "📅 No upcoming events found in your calendar."
            
            message = f"📅 Your Upcoming Events:\n\n"
            for event in calendar_data.events:
                message += f"📝 **{event['title']}**\n"
                message += f"   🕐 {event['start_time']}"
                if event['end_time'] != event['start_time']:
                    message += f" - {event['end_time']}"
                message += "\n"
                
                if event.get('location'):
                    message += f"   📍 {event['location']}\n"
                
                if event.get('description'):
                    # Truncate long descriptions
                    desc = event['description']
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    message += f"   📄 {desc}\n"
                
                message += "\n"
            
            return message.strip()
        
        elif calendar_data.action == "create":
            event = calendar_data.events[0] if calendar_data.events else {}
            message = f"✅ Event created successfully!\n\n"
            message += f"📝 **{event.get('title', 'New Event')}**\n"
            message += f"🕐 {event.get('start_time')} - {event.get('end_time')}\n"
            
            if event.get('location'):
                message += f"📍 {event['location']}\n"
            
            return message.strip()
        
        elif calendar_data.action == "update":
            return f"✅ Event updated successfully!"
        
        elif calendar_data.action == "delete":
            return f"✅ Event deleted successfully!"
        
        return calendar_data.message
    
    def parse_time_from_text(self, text: str) -> Optional[datetime]:
        """
        Parse datetime from natural language text.
        
        Args:
            text (str): Text containing time information
            
        Returns:
            Optional[datetime]: Parsed datetime or None
        """
        # This is a simplified implementation
        # In production, you might want to use libraries like dateutil.parser
        # or implement more sophisticated NLP parsing
        
        import re
        from dateutil import parser
        
        try:
            # Try to parse with dateutil
            parsed_time = parser.parse(text, fuzzy=True)
            return parsed_time
        except:
            pass
        
        # Handle relative times
        now = datetime.now()
        text_lower = text.lower()
        
        if "tomorrow" in text_lower:
            return now + timedelta(days=1)
        elif "next week" in text_lower:
            return now + timedelta(weeks=1)
        elif "next month" in text_lower:
            return now + timedelta(days=30)
        
        # Extract time patterns
        time_pattern = r'(\d{1,2}):(\d{2})\s*(am|pm)?'
        match = re.search(time_pattern, text_lower)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return None
    
    def get_calendar_intent_keywords(self) -> List[str]:
        """
        Get keywords that indicate calendar-related queries.
        
        Returns:
            List[str]: Calendar intent keywords
        """
        return [
            "calendar", "schedule", "meeting", "appointment", "event", "remind",
            "book", "plan", "agenda", "today", "tomorrow", "next week", "upcoming",
            "create event", "add to calendar", "what's on my calendar"
        ]
