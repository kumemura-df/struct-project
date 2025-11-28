"""Date parsing service for converting natural language dates to absolute dates."""
from datetime import datetime, timedelta
from typing import Optional
import dateparser
from dateutil import parser as dateutil_parser


def parse_date(
    date_text: str,
    reference_date: Optional[str] = None
) -> Optional[str]:
    """
    Parse a natural language date string to an absolute date.
    
    Args:
        date_text: Natural language date string (e.g., "next Friday", "tomorrow", "2024-12-25")
        reference_date: Reference date for relative dates (ISO format "YYYY-MM-DD")
    
    Returns:
        ISO format date string "YYYY-MM-DD" or None if parsing fails
    """
    if not date_text:
        return None
    
    # Parse reference date if provided
    ref_dt = None
    if reference_date:
        try:
            ref_dt = datetime.fromisoformat(reference_date)
        except (ValueError, TypeError):
            ref_dt = None
    
    # Try to parse with dateparser (handles natural language)
    settings = {
        'PREFER_DATES_FROM': 'future',  # Assume future dates by default
        'RETURN_AS_TIMEZONE_AWARE': False,
    }
    
    if ref_dt:
        settings['RELATIVE_BASE'] = ref_dt
    
    parsed = dateparser.parse(date_text, settings=settings)
    
    # If dateparser fails, try dateutil for strict ISO dates
    if not parsed:
        try:
            parsed = dateutil_parser.parse(date_text)
        except (ValueError, TypeError):
            return None
    
    # Return in ISO format
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    
    return None


def parse_date_with_meeting_context(
    date_text: str,
    meeting_date: str
) -> Optional[str]:
    """
    Parse a date with meeting date as context.
    
    Examples:
        - "next Friday" relative to meeting_date
        - "tomorrow" relative to meeting_date
        - "end of month" relative to meeting_date
    
    Args:
        date_text: Natural language date string
        meeting_date: Meeting date in ISO format "YYYY-MM-DD"
    
    Returns:
        ISO format date string "YYYY-MM-DD" or None if parsing fails
    """
    return parse_date(date_text, reference_date=meeting_date)
