"""Google Calendar integration for fetching meeting events."""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class GoogleCalendarClient:
    """Client for Google Calendar operations."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly',
    ]
    
    def __init__(self, credentials: Optional[Dict[str, Any]] = None):
        """Initialize with OAuth credentials."""
        self.credentials = credentials
        self._service = None
    
    def _get_service(self):
        """Get or create Calendar API service."""
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API client libraries not installed")
        
        if self._service is None:
            if not self.credentials:
                raise Exception("No credentials provided")
            
            creds = Credentials(
                token=self.credentials.get('access_token'),
                refresh_token=self.credentials.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('OAUTH_CLIENT_ID'),
                client_secret=os.getenv('OAUTH_CLIENT_SECRET'),
            )
            self._service = build('calendar', 'v3', credentials=creds)
        
        return self._service
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars accessible by the user."""
        service = self._get_service()
        
        calendars = []
        page_token = None
        
        while True:
            result = service.calendarList().list(pageToken=page_token).execute()
            calendars.extend(result.get('items', []))
            page_token = result.get('nextPageToken')
            if not page_token:
                break
        
        return calendars
    
    def list_events(
        self,
        calendar_id: str = 'primary',
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        limit: int = 20,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List calendar events.
        
        Args:
            calendar_id: Calendar ID ('primary' for main calendar)
            time_min: Start time in RFC3339 format
            time_max: End time in RFC3339 format
            limit: Maximum number of events
            search_query: Optional search term (e.g., "会議" for meetings)
            
        Returns:
            List of event dictionaries
        """
        service = self._get_service()
        
        # Default to past 30 days if not specified
        if not time_min:
            time_min = (datetime.utcnow() - timedelta(days=30)).isoformat() + 'Z'
        if not time_max:
            time_max = datetime.utcnow().isoformat() + 'Z'
        
        params = {
            'calendarId': calendar_id,
            'timeMin': time_min,
            'timeMax': time_max,
            'maxResults': limit,
            'singleEvents': True,
            'orderBy': 'startTime',
        }
        
        if search_query:
            params['q'] = search_query
        
        result = service.events().list(**params).execute()
        return result.get('items', [])
    
    def list_meeting_events(
        self,
        days_back: int = 30,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List events that are likely meetings.
        Filters for events with attendees or video conferencing.
        """
        time_min = (datetime.utcnow() - timedelta(days=days_back)).isoformat() + 'Z'
        time_max = datetime.utcnow().isoformat() + 'Z'
        
        events = self.list_events(
            time_min=time_min,
            time_max=time_max,
            limit=100  # Get more to filter
        )
        
        # Filter for meetings (events with attendees or conference data)
        meetings = []
        for event in events:
            has_attendees = len(event.get('attendees', [])) > 0
            has_conference = 'conferenceData' in event
            has_meet_link = 'hangoutLink' in event
            
            if has_attendees or has_conference or has_meet_link:
                meetings.append({
                    'id': event.get('id'),
                    'summary': event.get('summary', 'Untitled'),
                    'start': event.get('start', {}).get('dateTime') or event.get('start', {}).get('date'),
                    'end': event.get('end', {}).get('dateTime') or event.get('end', {}).get('date'),
                    'attendees_count': len(event.get('attendees', [])),
                    'has_video': has_conference or has_meet_link,
                    'meet_link': event.get('hangoutLink'),
                    'description': event.get('description', ''),
                })
        
        return meetings[:limit]
    
    def get_event(self, event_id: str, calendar_id: str = 'primary') -> Dict[str, Any]:
        """Get a specific event by ID."""
        service = self._get_service()
        return service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()


def is_available() -> bool:
    """Check if Google Calendar integration is available."""
    return GOOGLE_API_AVAILABLE

