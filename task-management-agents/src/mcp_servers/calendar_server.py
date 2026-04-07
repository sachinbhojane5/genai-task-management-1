"""MCP server for Google Calendar tools."""

from typing import Optional
from mcp.server.fastmcp import FastMCP

from src.services.calendar_service import CalendarService

# Initialize MCP server
calendar_mcp = FastMCP("Calendar Management Server")

# Initialize service
calendar_service = CalendarService()


def get_user_id() -> str:
    """Get current user ID from context."""
    return "default_user"


@calendar_mcp.tool()
async def create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: Optional[list[str]] = None,
    calendar_id: str = "primary",
) -> dict:
    """Create an event in Google Calendar.

    Args:
        title: Event title/summary
        start_time: Start time in ISO 8601 format (e.g., 2024-03-15T14:00:00Z)
        end_time: End time in ISO 8601 format
        description: Event description (optional)
        location: Event location (optional)
        attendees: List of attendee email addresses (optional)
        calendar_id: Calendar ID (default: primary)

    Returns:
        The created event with its ID and link
    """
    user_id = get_user_id()
    event = await calendar_service.create_event(
        user_id=user_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        description=description,
        location=location,
        attendees=attendees,
        calendar_id=calendar_id,
    )
    return event.to_dict()


@calendar_mcp.tool()
async def list_events(
    start_date: str,
    end_date: str,
    calendar_id: str = "primary",
    max_results: int = 50,
) -> list[dict]:
    """List events from Google Calendar in a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        calendar_id: Calendar ID (default: primary)
        max_results: Maximum number of events to return

    Returns:
        List of calendar events
    """
    user_id = get_user_id()
    events = await calendar_service.list_events(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        calendar_id=calendar_id,
        max_results=max_results,
    )
    return [event.to_dict() for event in events]


@calendar_mcp.tool()
async def get_event(
    event_id: str,
    calendar_id: str = "primary",
) -> Optional[dict]:
    """Get a specific calendar event by ID.

    Args:
        event_id: The unique event identifier
        calendar_id: Calendar ID (default: primary)

    Returns:
        The event details or None if not found
    """
    user_id = get_user_id()
    event = await calendar_service.get_event(
        user_id=user_id,
        event_id=event_id,
        calendar_id=calendar_id,
    )
    return event.to_dict() if event else None


@calendar_mcp.tool()
async def check_availability(
    date: str,
    duration_minutes: int,
    calendar_id: str = "primary",
) -> list[dict]:
    """Find available time slots on a given date.

    Checks the calendar's free/busy information and returns
    available time slots that can accommodate the requested duration.

    Args:
        date: Date to check in YYYY-MM-DD format
        duration_minutes: Required duration in minutes
        calendar_id: Calendar ID (default: primary)

    Returns:
        List of available time slots with start and end times
    """
    user_id = get_user_id()
    slots = await calendar_service.check_availability(
        user_id=user_id,
        date=date,
        duration_minutes=duration_minutes,
        calendar_id=calendar_id,
    )
    return slots


@calendar_mcp.tool()
async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
) -> dict:
    """Delete an event from Google Calendar.

    Args:
        event_id: The unique event identifier
        calendar_id: Calendar ID (default: primary)

    Returns:
        Status of the deletion operation
    """
    user_id = get_user_id()
    success = await calendar_service.delete_event(
        user_id=user_id,
        event_id=event_id,
        calendar_id=calendar_id,
    )
    return {"success": success, "event_id": event_id}


@calendar_mcp.tool()
async def get_todays_events(calendar_id: str = "primary") -> list[dict]:
    """Get all events scheduled for today.

    Args:
        calendar_id: Calendar ID (default: primary)

    Returns:
        List of today's calendar events
    """
    from datetime import date

    today = date.today().isoformat()
    user_id = get_user_id()

    events = await calendar_service.list_events(
        user_id=user_id,
        start_date=today,
        end_date=today,
        calendar_id=calendar_id,
    )
    return [event.to_dict() for event in events]


@calendar_mcp.tool()
async def get_upcoming_events(
    days: int = 7,
    calendar_id: str = "primary",
) -> list[dict]:
    """Get upcoming events for the next N days.

    Args:
        days: Number of days to look ahead (default: 7)
        calendar_id: Calendar ID (default: primary)

    Returns:
        List of upcoming calendar events
    """
    from datetime import date, timedelta

    today = date.today()
    end_date = today + timedelta(days=days)
    user_id = get_user_id()

    events = await calendar_service.list_events(
        user_id=user_id,
        start_date=today.isoformat(),
        end_date=end_date.isoformat(),
        calendar_id=calendar_id,
    )
    return [event.to_dict() for event in events]
